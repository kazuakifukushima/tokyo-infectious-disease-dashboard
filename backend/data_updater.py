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
        
        注意: このメソッドは統合データファイルから直接読み込むため、
        csv_list/に個別ファイルがなくても動作する
        """
        existing_keys = set()
        
        # まず processed_data を確認
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
                logger.info(f"既存データキー数（processed_data）: {len(existing_keys)}")
            except Exception as e:
                logger.error(f"既存データの読み込みエラー: {str(e)}")
        
        # 次に data/ ディレクトリも確認（Vercel用の静的ファイル）
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        data_file = os.path.join(data_dir, "infectious_diseases_data.csv")
        if os.path.exists(data_file) and data_file != main_data_file:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        key = (
                            int(row['year']),
                            int(row['week']),
                            row['disease_name']
                        )
                        existing_keys.add(key)
                logger.info(f"既存データキー数（data）: {len(existing_keys)}")
            except Exception as e:
                logger.error(f"data/ディレクトリのデータ読み込みエラー: {str(e)}")
        
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
        """既存の処理済みデータを読み込み（processed_data/とdata/の両方を確認）"""
        existing_data = []
        
        # まず processed_data を確認
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
                logger.info(f"既存データを読み込みました（processed_data）: {len(existing_data)} レコード")
            except Exception as e:
                logger.error(f"既存データの読み込みエラー（processed_data）: {str(e)}")
        
        # 次に data/ ディレクトリも確認（Vercel用の静的ファイル、GitHub Actions環境）
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        data_file = os.path.join(data_dir, "infectious_diseases_data.csv")
        if os.path.exists(data_file) and data_file != main_data_file:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 重複チェック: 既に読み込んだデータと重複していないか確認
                        key = (int(row['year']), int(row['week']), row['disease_name'])
                        if not any((d['year'], d['week'], d['disease_name']) == key for d in existing_data):
                            existing_data.append({
                                'disease_name': row['disease_name'],
                                'count': int(row['count']),
                                'year': int(row['year']),
                                'week': int(row['week']),
                                'report_date': row['report_date'],
                                'category': row['category']
                            })
                logger.info(f"既存データを読み込みました（data）: 合計 {len(existing_data)} レコード")
            except Exception as e:
                logger.error(f"data/ディレクトリのデータ読み込みエラー: {str(e)}")
        
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
            # 既存の処理済みデータを読み込み（最初に実行）
            existing_data = self.load_existing_data()
            existing_keys = self.get_existing_data_keys()
            logger.info(f"既存データキー数: {len(existing_keys)}")
            
            # 既存のCSVファイルリストを取得（後方互換性のため）
            existing_csv_files = get_existing_csv_files(self.csv_dir)
            logger.info(f"既存CSVファイル数: {len(existing_csv_files)}")
            
            # GitHubから新しいCSVファイルを取得して直接処理（ファイル保存なし）
            all_new_data = []
            processed_count_from_github = 0
            if not force_reprocess:
                # まず通常の方法を試す
                try:
                    csv_files = self.github_fetcher.get_recent_csv_files()
                    logger.info(f"GitHubから {len(csv_files)} 件のCSVファイル情報を取得しました")
                    
                    for file_info in csv_files:
                        filename = file_info["name"]
                        # ファイル名から年と週を抽出
                        date_info = self.data_processor._extract_date_from_filename(filename)
                        if not date_info:
                            continue
                        
                        # CSVコンテンツをメモリ上でダウンロード
                        csv_content_bytes = self.github_fetcher.download_file(file_info["download_url"])
                        if csv_content_bytes:
                            try:
                                # Shift-JISでデコード
                                csv_content = csv_content_bytes.decode('shift_jis')
                                # 直接処理
                                file_data = self.data_processor.process_csv_content(csv_content, filename)
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
                                        processed_count_from_github += 1
                                        logger.debug(f"GitHubから処理: {filename} - {len(new_records)} レコード追加")
                            except Exception as e:
                                logger.warning(f"CSVコンテンツの処理エラー {filename}: {str(e)}")
                    
                    result["downloaded_files"] = processed_count_from_github
                    logger.info(f"GitHubから {processed_count_from_github} 件のファイルを処理しました")
                    
                except Exception as e:
                    logger.warning(f"GitHubからの直接処理が失敗しました: {str(e)}")
                    # フォールバック: 既存のcsv_list/から処理
                    logger.info("既存のcsv_list/から処理を続行します...")
            else:
                logger.info("強制再処理モード: 既存ファイルを処理します")
            
            # 既存のcsv_list/ディレクトリにファイルがある場合のみ処理（後方互換性のため）
            if os.path.exists(self.csv_dir):
                csv_files = [
                    f for f in os.listdir(self.csv_dir)
                    if f.endswith('.csv') and f.startswith('notifiable_weekly_')
                ]
                
                if csv_files:
                    logger.info(f"既存のcsv_list/から {len(csv_files)} 件のファイルを処理します...")
                    
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
                    
                    logger.info(f"csv_list/処理完了: 新規データあり {processed_count} ファイル, スキップ {skipped_count} ファイル")
            else:
                logger.info("csv_list/ディレクトリが存在しないため、スキップします（GitHubから直接処理済み）")
            
            # データを統合
            if existing_data:
                merged_data = existing_data + all_new_data
                result["new_records"] = len(all_new_data)
                logger.info(f"既存データ {len(existing_data)} レコード + 新規データ {len(all_new_data)} レコード")
            else:
                merged_data = all_new_data
                result["new_records"] = len(merged_data)
                if merged_data:
                    logger.info(f"既存データなし、新規データ {len(merged_data)} レコード")
            
            result["total_records"] = len(merged_data)
            
            # 処理済みデータを保存（既存データがあれば統合データを、なければ新規データを保存）
            if merged_data:
                self.data_processor.save_processed_data(merged_data)
                result["success"] = True
                logger.info(f"データ更新が完了しました: 新規 {result['new_records']} レコード, 総計 {result['total_records']} レコード")
            elif existing_data:
                # 既存データのみがある場合も保存（データが更新されていない場合）
                self.data_processor.save_processed_data(existing_data)
                result["success"] = True
                result["total_records"] = len(existing_data)
                logger.info(f"既存データを保存しました: {len(existing_data)} レコード（新規データなし）")
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
            
            # 既存の定点把握疾患データから処理済みの年・週を取得
            sentinel_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            sentinel_csv_path = os.path.join(sentinel_output_dir, "sentinel_diseases_data.csv")
            existing_sentinel_data = []
            existing_sentinel_keys = set()
            
            if os.path.exists(sentinel_csv_path):
                try:
                    with open(sentinel_csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # 型変換を確実に行う
                            normalized_row = {
                                'disease_name': str(row.get('disease_name', '')),
                                'year': int(row.get('year', 0)),
                                'week': int(row.get('week', 0)),
                                'week_date': str(row.get('week_date', '')),
                                'male_count': int(row.get('male_count', 0)),
                                'female_count': int(row.get('female_count', 0)),
                                'total_count': int(row.get('total_count', 0)),
                                'sentinel_points': int(row.get('sentinel_points', 0)),
                                'data_type': str(row.get('data_type', 'gender'))
                            }
                            existing_sentinel_data.append(normalized_row)
                            key = (normalized_row['year'], normalized_row['week'], normalized_row['disease_name'])
                            if key[0] > 0 and key[1] > 0:
                                existing_sentinel_keys.add(key)
                    logger.info(f"既存定点把握疾患データキー数: {len(existing_sentinel_keys)}")
                except Exception as e:
                    logger.warning(f"既存定点把握疾患データの読み込みエラー: {str(e)}")
            
            # GitHubから新しい定点把握疾患CSVファイルを取得して直接処理（ファイル保存なし）
            processed_sentinel_from_github = 0
            new_sentinel_data = []
            if not force_reprocess:
                try:
                    # 最近の定点把握疾患CSVファイルを取得（raw URL優先）
                    sentinel_csv_files = self.github_fetcher.get_recent_sentinel_csv_files(max_files=200)
                    logger.info(f"GitHubから {len(sentinel_csv_files)} 件の定点把握疾患CSVファイル情報を取得しました")
                    
                    # sentinel_data_processorをインポート
                    try:
                        from sentinel_data_processor import read_sentinel_csv, parse_filename, EXCLUDED_DISEASES
                    except ImportError:
                        logger.error("sentinel_data_processorモジュールが利用できません")
                        result["errors"].append("sentinel_data_processorモジュールが利用できません")
                        return result
                    
                    # 一時的にダウンロードしたファイルを保存するリスト（処理後に削除）
                    temp_files = []
                    
                    for file_info in sentinel_csv_files:
                        filename = file_info["name"]
                        # ファイル名から年・週を抽出して重複チェック
                        file_info_parsed = parse_filename(filename)
                        if not file_info_parsed:
                            continue
                        
                        year, week = file_info_parsed['year'], file_info_parsed['week']
                        
                        # 重複チェック: 既存データに含まれているか確認
                        key = (year, week)
                        if any((int(d.get('year', 0)), int(d.get('week', 0))) == key for d in existing_sentinel_data):
                            logger.debug(f"既存データのためスキップ: {filename} ({year}-W{week:02d})")
                            continue
                        
                        # CSVコンテンツをメモリ上でダウンロード
                        csv_content_bytes = self.github_fetcher.download_file(file_info["download_url"])
                        if csv_content_bytes:
                            try:
                                # 一時ファイルとして保存（sentinel_data_processorがファイルパスを要求するため）
                                import tempfile
                                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv', dir=self.csv_dir if os.path.exists(self.csv_dir) else None) as tmp_file:
                                    tmp_file.write(csv_content_bytes)
                                    tmp_path = tmp_file.name
                                
                                temp_files.append(tmp_path)
                                
                                # ファイルを処理
                                headers, data_rows, period_info = read_sentinel_csv(tmp_path)
                                if data_rows and not period_info.get('is_aggregated', False):
                                    # データを処理済み形式に変換
                                    for row in data_rows:
                                        if len(row) >= 4:
                                            disease_name = row[0].strip()
                                            if disease_name and disease_name not in EXCLUDED_DISEASES:
                                                try:
                                                    male_count = int(row[1] or 0)
                                                    female_count = int(row[2] or 0)
                                                    total_count = int(row[3] or 0)
                                                    sentinel_points = int(row[4] or 0) if len(row) > 4 else 0
                                                    
                                                    new_sentinel_data.append({
                                                        'disease_name': disease_name,
                                                        'year': year,
                                                        'week': week,
                                                        'week_date': f"{year}-W{week:02d}",
                                                        'male_count': male_count,
                                                        'female_count': female_count,
                                                        'total_count': total_count,
                                                        'sentinel_points': sentinel_points,
                                                        'data_type': 'gender'
                                                    })
                                                except (ValueError, IndexError):
                                                    continue
                                    
                                    processed_sentinel_from_github += 1
                                    logger.info(f"GitHubから処理: {filename} ({year}-W{week:02d}) - {len(data_rows)} レコード")
                            except Exception as e:
                                logger.warning(f"定点把握疾患CSVコンテンツの処理エラー {filename}: {str(e)}")
                    
                    # 一時ファイルを削除
                    for tmp_path in temp_files:
                        try:
                            os.unlink(tmp_path)
                        except Exception as e:
                            logger.debug(f"一時ファイル削除エラー {tmp_path}: {str(e)}")
                    
                    result["downloaded_files"] = processed_sentinel_from_github
                    logger.info(f"GitHubから {processed_sentinel_from_github} 件の定点把握疾患ファイルを処理しました（新規データ: {len(new_sentinel_data)} レコード）")
                    
                except Exception as e:
                    logger.warning(f"GitHubからの定点把握疾患直接処理が失敗しました: {str(e)}")
                    result["errors"].append(f"ダウンロードエラー: {str(e)}")
            
            # 定点把握疾患データを処理
            try:
                # 新規データと既存データを統合
                all_sentinel_data = existing_sentinel_data + new_sentinel_data
                
                # sentinel_data_processorを使用してデータを処理
                # csv_list/にファイルがある場合のみ処理（後方互換性のため）
                if os.path.exists(self.csv_dir):
                    try:
                        csv_processed_data, diseases = process_gender_data(data_dir=self.csv_dir)
                        # CSVから処理したデータも統合（重複チェック）
                        if isinstance(csv_processed_data, list):
                            csv_keys = {(int(d.get('year', 0)), int(d.get('week', 0)), str(d.get('disease_name', ''))) for d in all_sentinel_data}
                            for record in csv_processed_data:
                                if isinstance(record, dict):
                                    key = (int(record.get('year', 0)), int(record.get('week', 0)), str(record.get('disease_name', '')))
                                    if key not in csv_keys:
                                        all_sentinel_data.append(record)
                                        csv_keys.add(key)
                        processed_data = all_sentinel_data
                    except Exception as e:
                        logger.warning(f"csv_list/からの処理でエラーが発生しました: {str(e)}")
                        processed_data = all_sentinel_data
                        diseases = sorted(list(set(str(row.get('disease_name', '')) for row in processed_data if row.get('disease_name'))))
                else:
                    # csv_list/がない場合は、既存データと新規データを使用
                    logger.info("csv_list/ディレクトリが存在しないため、既存データと新規データを使用します")
                    processed_data = all_sentinel_data
                    diseases = sorted(list(set(str(row.get('disease_name', '')) for row in processed_data if row.get('disease_name'))))
                
                if processed_data:
                    # 除外対象の疾病をフィルタリング（全数把握疾患など）
                    EXCLUDED_DISEASES = {'百日咳'}  # 5類感染症だが全数把握疾患のため除外
                    filtered_data = [
                        record for record in processed_data 
                        if record['disease_name'] not in EXCLUDED_DISEASES
                    ]
                    filtered_diseases = [
                        disease for disease in diseases 
                        if disease not in EXCLUDED_DISEASES
                    ]
                    
                    # データを保存
                    sentinel_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                    os.makedirs(sentinel_output_dir, exist_ok=True)
                    
                    # CSVファイルとして保存
                    sentinel_csv_path = os.path.join(sentinel_output_dir, "sentinel_diseases_data.csv")
                    with open(sentinel_csv_path, 'w', encoding='utf-8', newline='') as f:
                        if filtered_data:
                            writer = csv.DictWriter(f, fieldnames=filtered_data[0].keys())
                            writer.writeheader()
                            writer.writerows(filtered_data)
                    
                    # 疾病リストを保存
                    sentinel_disease_list_path = os.path.join(sentinel_output_dir, "sentinel_disease_list.json")
                    with open(sentinel_disease_list_path, 'w', encoding='utf-8') as f:
                        json.dump(filtered_diseases, f, ensure_ascii=False, indent=2)
                    
                    # サマリー統計を保存
                    disease_summary = create_disease_summary(filtered_data)
                    sentinel_summary_path = os.path.join(sentinel_output_dir, "sentinel_summary_statistics.json")
                    summary_data = {
                        "total_records": len(filtered_data),
                        "total_diseases": len(filtered_diseases),
                        "available_diseases": filtered_diseases,
                        "date_range": {
                            "start_year": min(int(d['year']) if isinstance(d.get('year'), str) else d.get('year', 0) for d in filtered_data) if filtered_data else None,
                            "end_year": max(int(d['year']) if isinstance(d.get('year'), str) else d.get('year', 0) for d in filtered_data) if filtered_data else None
                        },
                        "disease_statistics": disease_summary
                    }
                    with open(sentinel_summary_path, 'w', encoding='utf-8') as f:
                        json.dump(summary_data, f, ensure_ascii=False, indent=2)
                    
                    result["success"] = True
                    result["processed_files"] = int(len(filtered_data))
                    logger.info(f"定点把握疾患データ更新が完了しました: {len(filtered_data)} レコード（除外: {len(processed_data) - len(filtered_data)} レコード）")
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

