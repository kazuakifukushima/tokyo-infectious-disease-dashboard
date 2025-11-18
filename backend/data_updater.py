#!/usr/bin/env python3
"""
データ更新処理モジュール
GitHubリポジトリから新しいデータを取得し、既存データベースに統合
"""

import os
import csv
import json
import logging
from typing import List, Dict, Set, Optional
from datetime import datetime
from collections import defaultdict

from github_fetcher import GitHubFetcher, get_existing_csv_files, get_existing_sentinel_csv_files
from simple_data_processor import SimpleDataProcessor

# レート制限回避のため、rawダウンローダーもインポート
try:
    from github_raw_downloader import download_recent_files
    RAW_DOWNLOADER_AVAILABLE = True
except ImportError:
    RAW_DOWNLOADER_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataUpdater:
    """データ更新処理クラス"""
    
    def __init__(self, csv_dir: str = "../csv_list", output_dir: str = "processed_data"):
        self.csv_dir = csv_dir
        self.output_dir = output_dir
        self.github_fetcher = GitHubFetcher()
        self.data_processor = SimpleDataProcessor(csv_dir=csv_dir, output_dir=output_dir)
        
        # 出力ディレクトリを作成
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_existing_data_keys(self) -> Set[tuple]:
        """
        既存データのキーセットを取得（重複チェック用）
        キーは (year, week, disease_name) のタプル
        """
        existing_keys = set()
        
        main_data_file = os.path.join(self.output_dir, "infectious_diseases_data.csv")
        if os.path.exists(main_data_file):
            try:
                with open(main_data_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        key = (
                            int(row['year']),
                            int(row['week']),
                            row['disease_name']
                        )
                        existing_keys.add(key)
                logger.info(f"既存データキー数: {len(existing_keys)}")
            except Exception as e:
                logger.error(f"既存データの読み込みエラー: {str(e)}")
        
        return existing_keys
    
    def merge_data(self, existing_data: List[Dict], new_data: List[Dict]) -> List[Dict]:
        """
        既存データと新しいデータを統合（重複を除去）
        
        Args:
            existing_data: 既存のデータリスト
            new_data: 新しいデータリスト
        
        Returns:
            統合されたデータリスト
        """
        # 既存データのキーセットを作成
        existing_keys = {
            (d['year'], d['week'], d['disease_name'])
            for d in existing_data
        }
        
        # 新しいデータで重複していないもののみ追加
        merged_data = existing_data.copy()
        new_records_count = 0
        
        for record in new_data:
            key = (record['year'], record['week'], record['disease_name'])
            if key not in existing_keys:
                merged_data.append(record)
                existing_keys.add(key)
                new_records_count += 1
        
        logger.info(f"新しいレコード数: {new_records_count}")
        logger.info(f"統合後の総レコード数: {len(merged_data)}")
        
        return merged_data
    
    def load_existing_data(self) -> List[Dict]:
        """既存の処理済みデータを読み込み"""
        existing_data = []
        
        main_data_file = os.path.join(self.output_dir, "infectious_diseases_data.csv")
        if os.path.exists(main_data_file):
            try:
                with open(main_data_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing_data.append({
                            'disease_name': row['disease_name'],
                            'count': int(row['count']),
                            'year': int(row['year']),
                            'week': int(row['week']),
                            'report_date': row['report_date'],
                            'category': row['category']
                        })
                logger.info(f"既存データを読み込みました: {len(existing_data)} レコード")
            except Exception as e:
                logger.error(f"既存データの読み込みエラー: {str(e)}")
        
        return existing_data
    
    def update_data(self, force_reprocess: bool = False) -> Dict:
        """
        データを更新
        
        Args:
            force_reprocess: Trueの場合、既存ファイルも再処理
        
        Returns:
            更新結果の辞書
        """
        logger.info("データ更新処理を開始します...")
        
        result = {
            "success": False,
            "downloaded_files": 0,
            "processed_files": 0,
            "new_records": 0,
            "total_records": 0,
            "errors": []
        }
        
        try:
            # 既存のCSVファイルリストを取得
            existing_csv_files = get_existing_csv_files(self.csv_dir)
            logger.info(f"既存CSVファイル数: {len(existing_csv_files)}")
            
            # GitHubから新しいCSVファイルをダウンロード
            downloaded_files = []
            if not force_reprocess:
                # まず通常の方法を試す
                try:
                    downloaded_files = self.github_fetcher.download_new_csv_files(
                        self.csv_dir,
                        existing_files=existing_csv_files,
                        use_recent_only=True
                    )
                except Exception as e:
                    logger.warning(f"通常のダウンロード方法が失敗しました: {str(e)}")
                    # レート制限の場合は、rawダウンローダーを使用
                    if RAW_DOWNLOADER_AVAILABLE:
                        logger.info("rawダウンローダーを使用してファイルを取得します...")
                        try:
                            downloaded_files = download_recent_files(
                                csv_dir=self.csv_dir,
                                existing_files=existing_csv_files
                            )
                        except Exception as e2:
                            logger.error(f"rawダウンローダーも失敗しました: {str(e2)}")
                            downloaded_files = []
                    else:
                        downloaded_files = []
                
                result["downloaded_files"] = len(downloaded_files)
                
                # ダウンロードしたファイルがない場合でも、処理を続行（未処理ファイルがある可能性がある）
                if not downloaded_files:
                    logger.info("新しいダウンロードファイルはありませんでした。既存ファイルを処理します...")
            else:
                logger.info("強制再処理モード: すべてのファイルを処理します")
            
            # 既存の処理済みデータを読み込み
            existing_data = self.load_existing_data()
            existing_keys = self.get_existing_data_keys()
            logger.info(f"既存データキー数: {len(existing_keys)}")
            
            # すべてのCSVファイルを処理
            logger.info("CSVファイルの処理を開始します...")
            all_new_data = []
            
            csv_files = [
                f for f in os.listdir(self.csv_dir)
                if f.endswith('.csv') and f.startswith('notifiable_weekly_')
            ]
            
            logger.info(f"処理対象ファイル数: {len(csv_files)}")
            
            processed_count = 0
            skipped_count = 0
            
            for filename in sorted(csv_files):
                filepath = os.path.join(self.csv_dir, filename)
                try:
                    file_data = self.data_processor.process_csv_file(filepath)
                    if file_data:
                        # 重複チェック: 既存データに含まれていないレコードのみを追加
                        new_records = []
                        for record in file_data:
                            key = (record['year'], record['week'], record['disease_name'])
                            if key not in existing_keys:
                                new_records.append(record)
                                existing_keys.add(key)
                        
                        if new_records:
                            all_new_data.extend(new_records)
                            processed_count += 1
                        else:
                            skipped_count += 1
                            
                        result["processed_files"] += 1
                except Exception as e:
                    error_msg = f"ファイル処理エラー {filename}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            logger.info(f"処理完了: 新規データあり {processed_count} ファイル, スキップ {skipped_count} ファイル")
            
            # データを統合
            if existing_data:
                merged_data = existing_data + all_new_data
                result["new_records"] = len(all_new_data)
            else:
                merged_data = all_new_data
                result["new_records"] = len(merged_data)
            
            result["total_records"] = len(merged_data)
            
            # 処理済みデータを保存
            if merged_data:
                self.data_processor.save_processed_data(merged_data)
                result["success"] = True
                logger.info(f"データ更新が完了しました: 新規 {result['new_records']} レコード, 総計 {result['total_records']} レコード")
            else:
                logger.warning("保存するデータがありませんでした")
                result["errors"].append("保存するデータがありませんでした")
            
            # 定点把握疾患データも更新
            logger.info("定点把握疾患データの更新を開始します...")
            sentinel_result = self.update_sentinel_data(force_reprocess=force_reprocess)
            if sentinel_result.get("success"):
                logger.info(f"定点把握疾患データ更新成功: {sentinel_result.get('processed_files', 0)} レコード")
            else:
                logger.warning(f"定点把握疾患データ更新に問題がありました: {sentinel_result.get('errors', [])}")
                # エラーは記録するが、全体の処理は続行
                result["errors"].extend([f"定点把握疾患: {e}" for e in sentinel_result.get("errors", [])])
            
        except Exception as e:
            error_msg = f"データ更新処理中にエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False
        
        return result
    
    def update_sentinel_data(self, force_reprocess: bool = False) -> Dict:
        """
        定点把握疾患データを更新
        
        Args:
            force_reprocess: Trueの場合、既存ファイルも再処理
        
        Returns:
            更新結果の辞書
        """
        logger.info("定点把握疾患データ更新処理を開始します...")
        
        result = {
            "success": False,
            "downloaded_files": 0,
            "processed_files": 0,
            "errors": []
        }
        
        try:
            # 定点把握疾患データ処理モジュールをインポート
            try:
                from sentinel_data_processor import process_gender_data, create_disease_summary
            except ImportError:
                logger.error("sentinel_data_processorモジュールが利用できません")
                result["errors"].append("sentinel_data_processorモジュールが利用できません")
                return result
            
            # 既存の定点把握疾患CSVファイルリストを取得
            existing_sentinel_files = get_existing_sentinel_csv_files(self.csv_dir)
            logger.info(f"既存定点把握疾患CSVファイル数: {len(existing_sentinel_files)}")
            
            # GitHubから新しい定点把握疾患CSVファイルをダウンロード
            downloaded_files = []
            if not force_reprocess:
                try:
                    # 最近の定点把握疾患CSVファイルを取得
                    sentinel_csv_files = self.github_fetcher.get_recent_sentinel_csv_files()
                    
                    for file_info in sentinel_csv_files:
                        filename = file_info["name"]
                        if filename not in existing_sentinel_files:
                            save_path = os.path.join(self.csv_dir, filename)
                            if self.github_fetcher.download_file(file_info["download_url"], save_path):
                                downloaded_files.append(save_path)
                    
                    # 既存ファイルから最新の週を確認し、不足している週のファイルを直接ダウンロード
                    import re
                    existing_weeks = set()
                    for filename in existing_sentinel_files:
                        match = re.search(r'sentinel_weekly_gender_2025_(\d+)', filename)
                        if match:
                            existing_weeks.add(int(match.group(1)))
                    
                    # 2025年の最新週を確認（第47週まで）
                    current_year = 2025
                    max_week = 47  # 現在の最新週
                    
                    # 不足している週のファイルを直接ダウンロード
                    missing_weeks = []
                    for week in range(1, max_week + 1):
                        if week not in existing_weeks:
                            missing_weeks.append(week)
                    
                    if missing_weeks:
                        logger.info(f"不足している週のファイルを直接ダウンロードします: {len(missing_weeks)}週分")
                        import requests
                        raw_base_url = f"https://raw.githubusercontent.com/{self.github_fetcher.repo_owner}/{self.github_fetcher.repo_name}/main/data/raw"
                        
                        for week in missing_weeks[:30]:  # 一度に30週まで（レート制限対策）
                            filename = f"sentinel_weekly_gender_{current_year}_{week}.csv"
                            if filename not in existing_sentinel_files:
                                url = f"{raw_base_url}/{filename}"
                                save_path = os.path.join(self.csv_dir, filename)
                                
                                try:
                                    response = requests.get(url, timeout=10)
                                    if response.status_code == 200:
                                        with open(save_path, 'wb') as f:
                                            f.write(response.content)
                                        downloaded_files.append(save_path)
                                        logger.debug(f"直接ダウンロード成功: {filename}")
                                except Exception as e:
                                    logger.debug(f"直接ダウンロード失敗 {filename}: {str(e)}")
                    
                    result["downloaded_files"] = len(downloaded_files)
                    logger.info(f"定点把握疾患ファイルを {len(downloaded_files)} 件ダウンロードしました")
                except Exception as e:
                    logger.warning(f"定点把握疾患ファイルのダウンロードが失敗しました: {str(e)}")
                    result["errors"].append(f"ダウンロードエラー: {str(e)}")
            
            # 定点把握疾患データを処理
            try:
                # sentinel_data_processorを使用してデータを処理
                processed_data, diseases = process_gender_data(data_dir=self.csv_dir)
                
                if processed_data:
                    # データを保存
                    sentinel_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                    os.makedirs(sentinel_output_dir, exist_ok=True)
                    
                    # CSVファイルとして保存
                    sentinel_csv_path = os.path.join(sentinel_output_dir, "sentinel_diseases_data.csv")
                    with open(sentinel_csv_path, 'w', encoding='utf-8', newline='') as f:
                        if processed_data:
                            writer = csv.DictWriter(f, fieldnames=processed_data[0].keys())
                            writer.writeheader()
                            writer.writerows(processed_data)
                    
                    # 疾病リストを保存
                    sentinel_disease_list_path = os.path.join(sentinel_output_dir, "sentinel_disease_list.json")
                    with open(sentinel_disease_list_path, 'w', encoding='utf-8') as f:
                        json.dump(list(diseases), f, ensure_ascii=False, indent=2)
                    
                    # サマリー統計を保存
                    disease_summary = create_disease_summary(processed_data)
                    sentinel_summary_path = os.path.join(sentinel_output_dir, "sentinel_summary_statistics.json")
                    summary_data = {
                        "total_records": len(processed_data),
                        "total_diseases": len(diseases),
                        "available_diseases": list(diseases),
                        "date_range": {
                            "start_year": min(d['year'] for d in processed_data) if processed_data else None,
                            "end_year": max(d['year'] for d in processed_data) if processed_data else None
                        },
                        "disease_statistics": disease_summary
                    }
                    with open(sentinel_summary_path, 'w', encoding='utf-8') as f:
                        json.dump(summary_data, f, ensure_ascii=False, indent=2)
                    
                    result["success"] = True
                    result["processed_files"] = len(processed_data)
                    logger.info(f"定点把握疾患データ更新が完了しました: {len(processed_data)} レコード")
                else:
                    logger.warning("処理する定点把握疾患データがありませんでした")
                    result["errors"].append("処理するデータがありませんでした")
                    
            except Exception as e:
                error_msg = f"定点把握疾患データ処理エラー: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False
            
        except Exception as e:
            error_msg = f"定点把握疾患データ更新処理中にエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["success"] = False
        
        return result
    
    def get_update_status(self) -> Dict:
        """更新状態を取得"""
        try:
            # GitHubリポジトリの最新コミットSHAを取得
            latest_sha = self.github_fetcher.get_latest_commit_sha()
            
            # ローカルの状態を取得
            existing_data = self.load_existing_data()
            existing_csv_files = get_existing_csv_files(self.csv_dir)
            existing_sentinel_files = get_existing_sentinel_csv_files(self.csv_dir)
            
            # 最後の更新日時を取得
            main_data_file = os.path.join(self.output_dir, "infectious_diseases_data.csv")
            last_modified = None
            if os.path.exists(main_data_file):
                last_modified = datetime.fromtimestamp(
                    os.path.getmtime(main_data_file)
                ).isoformat()
            
            return {
                "latest_commit_sha": latest_sha,
                "local_records": len(existing_data),
                "local_csv_files": len(existing_csv_files),
                "local_sentinel_csv_files": len(existing_sentinel_files),
                "last_updated": last_modified,
                "data_file_exists": os.path.exists(main_data_file)
            }
        except Exception as e:
            logger.error(f"更新状態の取得エラー: {str(e)}")
            return {
                "error": str(e)
            }


def main():
    """メイン実行関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = DataUpdater()
    
    # 更新状態を確認
    print("=== 更新状態 ===")
    status = updater.get_update_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # データを更新
    print("\n=== データ更新 ===")
    result = updater.update_data()
    
    print("\n=== 更新結果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

