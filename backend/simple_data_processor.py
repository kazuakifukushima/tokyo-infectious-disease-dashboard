#!/usr/bin/env python3
"""
簡易版データ処理スクリプト
標準ライブラリのみを使用してCSVファイルを処理します。
"""

import os
import csv
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDataProcessor:
    def __init__(self, csv_dir: str = "../csv_list", output_dir: str = "processed_data"):
        self.csv_dir = csv_dir
        self.output_dir = output_dir
        self.disease_categories = self._load_disease_categories()
        
        # 出力ディレクトリ作成
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _load_disease_categories(self):
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
                "炭疽", "チクングニア熱", "デング熱", "東部ウマ脳炎",
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
    
    def _extract_date_from_filename(self, filename):
        """ファイル名から年と週番号を抽出"""
        # notifiable_weekly_2000_1_20250703_031821_raw.csv の形式
        pattern = r'notifiable_weekly_(\d{4})_(\d+)_\d+_\d+_raw\.csv'
        match = re.match(pattern, filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None
    
    def _week_to_date(self, year, week):
        """年と週番号から日付を計算"""
        jan1 = datetime(year, 1, 1)
        days_to_first_monday = (7 - jan1.weekday()) % 7
        first_monday = jan1 + timedelta(days=days_to_first_monday)
        target_date = first_monday + timedelta(weeks=week-1)
        return target_date.isoformat()
    
    def _get_disease_category(self, disease_name):
        """疾病名から法定分類を取得"""
        for category, diseases in self.disease_categories.items():
            if disease_name in diseases:
                return category
        return "その他"
    
    def process_csv_file(self, filepath):
        """単一のCSVファイルを処理"""
        try:
            filename = os.path.basename(filepath)
            date_info = self._extract_date_from_filename(filename)
            if not date_info:
                logger.warning(f"日付情報を抽出できませんでした: {filename}")
                return []
            
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
                return []
            
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
                            if disease_name:
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
            
            return disease_data
                
        except Exception as e:
            logger.error(f"ファイル処理中にエラーが発生しました {filepath}: {str(e)}")
            return []
    
    def process_all_files(self):
        """すべてのCSVファイルを処理"""
        logger.info("CSVファイルの処理を開始します...")
        
        csv_files = [f for f in os.listdir(self.csv_dir) if f.endswith('_raw.csv') and f.startswith('notifiable_weekly_')]
        logger.info(f"処理対象ファイル数: {len(csv_files)}")
        
        all_data = []
        processed_count = 0
        
        for filename in csv_files:
            filepath = os.path.join(self.csv_dir, filename)
            data = self.process_csv_file(filepath)
            if data:
                all_data.extend(data)
                processed_count += 1
                
                if processed_count % 100 == 0:
                    logger.info(f"処理済み: {processed_count}/{len(csv_files)}")
        
        logger.info(f"統合完了: {len(all_data)} レコード")
        return all_data
    
    def generate_summary_statistics(self, data):
        """サマリー統計を生成"""
        if not data:
            return {}
        
        # 基本統計
        years = set(d['year'] for d in data)
        diseases = set(d['disease_name'] for d in data)
        categories = defaultdict(int)
        top_diseases = defaultdict(int)
        yearly_totals = defaultdict(int)
        
        min_date = min(d['report_date'] for d in data)
        max_date = max(d['report_date'] for d in data)
        
        for record in data:
            categories[record['category']] += record['count']
            top_diseases[record['disease_name']] += record['count']
            yearly_totals[str(record['year'])] += record['count']
        
        # 上位10疾病を取得
        top_diseases_sorted = dict(sorted(top_diseases.items(), key=lambda x: x[1], reverse=True)[:10])
        
        summary = {
            'total_records': len(data),
            'date_range': {
                'start': min_date,
                'end': max_date
            },
            'years_covered': sorted(list(years)),
            'total_diseases': len(diseases),
            'disease_categories': dict(categories),
            'top_diseases': top_diseases_sorted,
            'yearly_totals': dict(yearly_totals)
        }
        
        return summary
    
    def save_processed_data(self, data):
        """処理済みデータを保存"""
        if not data:
            logger.error("保存するデータがありません")
            return
        
        # メインデータセットを保存（CSV形式）
        main_file = os.path.join(self.output_dir, 'infectious_diseases_data.csv')
        with open(main_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['disease_name', 'count', 'year', 'week', 'report_date', 'category']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"メインデータセットを保存しました: {main_file}")
        
        # サマリー統計を保存
        summary = self.generate_summary_statistics(data)
        summary_file = os.path.join(self.output_dir, 'summary_statistics.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"サマリー統計を保存しました: {summary_file}")
        
        # 疾病リストを保存
        disease_list = sorted(list(set(d['disease_name'] for d in data)))
        disease_file = os.path.join(self.output_dir, 'disease_list.json')
        with open(disease_file, 'w', encoding='utf-8') as f:
            json.dump(disease_list, f, ensure_ascii=False, indent=2)
        logger.info(f"疾病リストを保存しました: {disease_file}")
        
        logger.info("データ処理が完了しました")

def main():
    """メイン実行関数"""
    processor = SimpleDataProcessor()
    
    # すべてのファイルを処理
    data = processor.process_all_files()
    
    # 処理済みデータを保存
    processor.save_processed_data(data)
    
    print("\n=== 処理結果 ===")
    if data:
        print(f"総レコード数: {len(data):,}")
        
        years = set(d['year'] for d in data)
        print(f"期間: {min(years)} - {max(years)}")
        
        diseases = set(d['disease_name'] for d in data)
        print(f"疾病数: {len(diseases)}")
        
        print(f"対象年数: {len(years)}")
        
        # 上位疾病を表示
        disease_counts = defaultdict(int)
        for d in data:
            disease_counts[d['disease_name']] += d['count']
        
        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print("\n主要疾病（報告数上位10）:")
        for disease, count in top_diseases:
            print(f"  {disease}: {count:,}")
    else:
        print("処理可能なデータがありませんでした")

if __name__ == "__main__":
    main()