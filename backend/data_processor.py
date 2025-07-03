#!/usr/bin/env python3
"""
東京都感染症データ処理スクリプト
CSVファイルを読み込み、統合されたデータセットを生成します。
"""

import os
import pandas as pd
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfectiousDiseaseDataProcessor:
    def __init__(self, csv_dir: str = "csv_list", output_dir: str = "processed_data"):
        self.csv_dir = csv_dir
        self.output_dir = output_dir
        self.disease_categories = self._load_disease_categories()
        
        # 出力ディレクトリ作成
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _load_disease_categories(self) -> Dict[str, List[str]]:
        """感染症の法定分類を定義"""
        return {
            "1類感染症": [
                "エボラ出血熱", "クリミア・コンゴ出血熱", "痘そう", "南米出血熱", 
                "ペスト", "マールブルグ病", "ラッサ熱"
            ],
            "2類感染症": [
                "急性灰白髄炎", "結核", "ジフテリア", "重症急性呼吸器症候群", 
                "中東呼吸器症候群", "鳥インフルエンザ（H5N1)", "鳥インフルエンザ（H7N9)"
            ],
            "3類感染症": [
                "コレラ", "細菌性赤痢", "腸チフス", "パラチフス"
            ],
            "4類感染症": [
                "A型肝炎", "E型肝炎", "つつが虫病", "ウイルス性肝炎（Ｅ型肝炎及びＡ型肝炎を除く。）",
                "ウエストナイル熱", "エキノコックス症", "オウム病", "オムスク出血熱",
                "回帰熱", "Ｑ熱", "狂犬病", "コクシジオイデス症", "ジカウイルス感染症",
                "重症熱性血小板減少症候群", "腎症候性出血熱", "西部ウマ脳炎", "ダニ媒介脳炎",
                "炭疽", "チクングニア熱", "つつが虫病", "デング熱", "東部ウマ脳炎",
                "鳥インフルエンザ（H5N1およびH7N9を除く）", "ニパウイルス感染症", "日本紅斑熱", 
                "日本脳炎", "ハンタウイルス肺症候群", "Ｂウイルス病", "鼻疽", "ブルセラ症",
                "ベネズエラウマ脳炎", "ヘンドラウイルス感染症", "発しんチフス", "ボツリヌス症",
                "マラリア", "野兎病", "ライム病", "リッサウイルス感染症", "リフトバレー熱",
                "類鼻疽", "レジオネラ症", "レプトスピラ症", "ロッキー山紅斑熱", "黄熱"
            ],
            "5類感染症": [
                "アメーバ赤痢", "ウイルス性肝炎（Ｅ型肝炎及びＡ型肝炎を除く。）", 
                "カルバペネム耐性腸内細菌目細菌感染症", "急性弛緩性麻痺（急性灰白髄炎を除く。）",
                "急性脳炎", "クリプトスポリジウム症", "クロイツフェルト・ヤコブ病", 
                "劇症型溶血性レンサ球菌感染症", "後天性免疫不全症候群", "ジアルジア症",
                "侵襲性インフルエンザ菌感染症", "侵襲性肺炎球菌感染症", "侵襲性髄膜炎菌感染症",
                "水痘（入院例に限る）", "先天性風しん症候群", "梅毒", "播種性クリプトコックス症",
                "バンコマイシン耐性腸球菌感染症", "バンコマイシン耐性黄色ブドウ球菌感染症",
                "百日咳", "風しん", "麻しん", "薬剤耐性アシネトバクター感染症", 
                "腸管出血性大腸菌感染症", "髄膜炎菌性髄膜炎"
            ]
        }
    
    def _extract_date_from_filename(self, filename: str) -> Optional[tuple]:
        """ファイル名から年と週番号を抽出"""
        pattern = r'notifiable_weekly_(\d{4})_(\d+)_\d+_raw\.csv'
        match = re.match(pattern, filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None
    
    def _week_to_date(self, year: int, week: int) -> datetime:
        """年と週番号から日付を計算"""
        # 年の1月1日を基準に週数を計算
        jan1 = datetime(year, 1, 1)
        # 1月1日の曜日を考慮して週の開始日を計算
        days_to_first_monday = (7 - jan1.weekday()) % 7
        first_monday = jan1 + timedelta(days=days_to_first_monday)
        target_date = first_monday + timedelta(weeks=week-1)
        return target_date
    
    def process_csv_file(self, filepath: str) -> Optional[pd.DataFrame]:
        """単一のCSVファイルを処理"""
        try:
            # ファイル名から年と週を抽出
            filename = os.path.basename(filepath)
            date_info = self._extract_date_from_filename(filename)
            if not date_info:
                logger.warning(f"日付情報を抽出できませんでした: {filename}")
                return None
            
            year, week = date_info
            report_date = self._week_to_date(year, week)
            
            # CSVファイルを読み込み（Shift-JIS エンコーディング）
            with open(filepath, 'r', encoding='shift_jis') as f:
                lines = f.readlines()
            
            # 疾病データの開始行を見つける
            data_start = None
            for i, line in enumerate(lines):
                if '疾病名' in line and '報告数' in line:
                    data_start = i + 1
                    break
            
            if data_start is None:
                logger.warning(f"疾病データが見つかりませんでした: {filename}")
                return None
            
            # 疾病データを抽出
            disease_data = []
            for line in lines[data_start:]:
                line = line.strip()
                if line and ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        disease_name = parts[0].strip('"')
                        try:
                            count = int(parts[1].strip('"'))
                            if disease_name:  # 空の疾病名は除外
                                disease_data.append({
                                    'disease_name': disease_name,
                                    'count': count,
                                    'year': year,
                                    'week': week,
                                    'report_date': report_date,
                                    'category': self._get_disease_category(disease_name)
                                })
                        except ValueError:
                            continue
            
            if disease_data:
                return pd.DataFrame(disease_data)
            else:
                logger.warning(f"有効な疾病データが見つかりませんでした: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"ファイル処理中にエラーが発生しました {filepath}: {str(e)}")
            return None
    
    def _get_disease_category(self, disease_name: str) -> str:
        """疾病名から法定分類を取得"""
        for category, diseases in self.disease_categories.items():
            if disease_name in diseases:
                return category
        return "その他"
    
    def process_all_files(self) -> pd.DataFrame:
        """すべてのCSVファイルを処理"""
        logger.info("CSVファイルの処理を開始します...")
        
        csv_files = [f for f in os.listdir(self.csv_dir) if f.endswith('_raw.csv')]
        logger.info(f"処理対象ファイル数: {len(csv_files)}")
        
        all_data = []
        processed_count = 0
        
        for filename in csv_files:
            filepath = os.path.join(self.csv_dir, filename)
            df = self.process_csv_file(filepath)
            if df is not None:
                all_data.append(df)
                processed_count += 1
                
                if processed_count % 100 == 0:
                    logger.info(f"処理済み: {processed_count}/{len(csv_files)}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"統合完了: {len(combined_df)} レコード")
            return combined_df
        else:
            logger.error("処理可能なファイルがありませんでした")
            return pd.DataFrame()
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """サマリー統計を生成"""
        if df.empty:
            return {}
        
        summary = {
            'total_records': len(df),
            'date_range': {
                'start': df['report_date'].min().isoformat(),
                'end': df['report_date'].max().isoformat()
            },
            'years_covered': sorted(df['year'].unique().tolist()),
            'total_diseases': df['disease_name'].nunique(),
            'disease_categories': df['category'].value_counts().to_dict(),
            'top_diseases': df.groupby('disease_name')['count'].sum().sort_values(ascending=False).head(10).to_dict(),
            'yearly_totals': df.groupby('year')['count'].sum().to_dict()
        }
        
        return summary
    
    def save_processed_data(self, df: pd.DataFrame):
        """処理済みデータを保存"""
        if df.empty:
            logger.error("保存するデータがありません")
            return
        
        # メインデータセットを保存
        main_file = os.path.join(self.output_dir, 'infectious_diseases_data.csv')
        df.to_csv(main_file, index=False, encoding='utf-8')
        logger.info(f"メインデータセットを保存しました: {main_file}")
        
        # サマリー統計を保存
        summary = self.generate_summary_statistics(df)
        summary_file = os.path.join(self.output_dir, 'summary_statistics.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"サマリー統計を保存しました: {summary_file}")
        
        # 疾病リストを保存
        disease_list = sorted(df['disease_name'].unique().tolist())
        disease_file = os.path.join(self.output_dir, 'disease_list.json')
        with open(disease_file, 'w', encoding='utf-8') as f:
            json.dump(disease_list, f, ensure_ascii=False, indent=2)
        logger.info(f"疾病リストを保存しました: {disease_file}")
        
        # 年別データを保存
        for year in df['year'].unique():
            year_df = df[df['year'] == year]
            year_file = os.path.join(self.output_dir, f'data_{year}.csv')
            year_df.to_csv(year_file, index=False, encoding='utf-8')
        
        logger.info("データ処理が完了しました")

def main():
    """メイン実行関数"""
    processor = InfectiousDiseaseDataProcessor()
    
    # すべてのファイルを処理
    df = processor.process_all_files()
    
    # 処理済みデータを保存
    processor.save_processed_data(df)
    
    print("\n=== 処理結果 ===")
    if not df.empty:
        print(f"総レコード数: {len(df):,}")
        print(f"期間: {df['report_date'].min()} - {df['report_date'].max()}")
        print(f"疾病数: {df['disease_name'].nunique()}")
        print(f"対象年数: {df['year'].nunique()}")
        print("\n主要疾病（報告数上位10）:")
        top_diseases = df.groupby('disease_name')['count'].sum().sort_values(ascending=False).head(10)
        for disease, count in top_diseases.items():
            print(f"  {disease}: {count:,}")
    else:
        print("処理可能なデータがありませんでした")

if __name__ == "__main__":
    main()