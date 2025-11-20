#!/usr/bin/env python3
"""
定点サーベイランスデータ処理スクリプト
Sentinel surveillance data processor for IDSC dashboard
"""

import csv
import json
import os
import re
from datetime import datetime
from collections import defaultdict
import glob

def parse_filename(filename):
    """
    ファイル名からメタデータを抽出
    例: 
    - sentinel_weekly_gender_2020_17_20250703_031821_raw.csv
    - sentinel_weekly_gender_2025_47.csv
    """
    basename = os.path.basename(filename)
    
    # パターン1: _raw.csv サフィックス付き
    pattern1 = r'sentinel_weekly_(\w+)_(\d{4})_(\d+)_\d+_\d+_raw\.csv'
    match = re.match(pattern1, basename)
    
    if match:
        data_type = match.group(1)  # gender, age, health_center, medical_district
        year = int(match.group(2))
        week = int(match.group(3))
        return {
            'data_type': data_type,
            'year': year,
            'week': week
        }
    
    # パターン2: 通常の .csv ファイル（例: sentinel_weekly_gender_2025_47.csv）
    pattern2 = r'sentinel_weekly_(\w+)_(\d{4})_(\d+)\.csv'
    match = re.match(pattern2, basename)
    
    if match:
        data_type = match.group(1)
        year = int(match.group(2))
        week = int(match.group(3))
        return {
            'data_type': data_type,
            'year': year,
            'week': week
        }
    
    return None

def read_sentinel_csv(filepath):
    """
    Shift-JISエンコードのSentinelCSVファイルを読み込み
    集計期間情報も返す
    
    Returns:
        (headers, data_rows, period_info): ヘッダー、データ行、集計期間情報
        period_info: {'start_week': int, 'end_week': int, 'is_aggregated': bool}
    """
    try:
        with open(filepath, 'r', encoding='shift-jis') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # 集計期間情報を読み取る
        period_info = {'start_week': None, 'end_week': None, 'is_aggregated': False}
        for i, row in enumerate(rows[:10]):
            if len(row) >= 2:
                if '集計期間開始週' in row[0] or '集計期間開始' in row[0]:
                    # 例: ['集計期間開始週', '2025年45週'] から週番号を抽出
                    week_str = row[1] if len(row) > 1 else ''
                    import re
                    match = re.search(r'(\d+)週', week_str)
                    if match:
                        period_info['start_week'] = int(match.group(1))
                elif '集計期間終了週' in row[0] or '集計期間終了' in row[0]:
                    week_str = row[1] if len(row) > 1 else ''
                    import re
                    match = re.search(r'(\d+)週', week_str)
                    if match:
                        period_info['end_week'] = int(match.group(1))
        
        # 開始週と終了週が異なる場合は合算データ
        if period_info['start_week'] is not None and period_info['end_week'] is not None:
            period_info['is_aggregated'] = period_info['start_week'] != period_info['end_week']
            
        # ヘッダー行を見つける
        header_row_idx = -1
        for i, row in enumerate(rows):
            if len(row) > 0 and '疾病名' in row[0]:
                header_row_idx = i
                break
        
        if header_row_idx == -1:
            return None, None, period_info
            
        # ヘッダーを取得
        headers = rows[header_row_idx]
        
        # データ行を取得
        data_rows = []
        for i in range(header_row_idx + 1, len(rows)):
            row = rows[i]
            if len(row) > 0 and row[0].strip() and not row[0].startswith('"'):
                # 空でない行のみを追加
                cleaned_row = [cell.strip().replace('"', '') for cell in row]
                if cleaned_row[0] and cleaned_row[0] != '疾病名':
                    data_rows.append(cleaned_row)
        
        return headers, data_rows, period_info
        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None, None, {'start_week': None, 'end_week': None, 'is_aggregated': False}

# 定点把握疾患から除外する疾病（全数把握疾患など）
EXCLUDED_DISEASES = {
    '百日咳',  # 5類感染症だが全数把握疾患のため除外
}

def process_gender_data(data_dir: str = '../csv_list'):
    """
    男女別データを処理してインフルエンザなどの主要疾患を抽出
    
    Args:
        data_dir: CSVファイルが保存されているディレクトリパス
    
    Returns:
        (processed_data, diseases_found): 処理済みデータのリストと疾病名のセット
    """
    # _raw.csv と通常の .csv の両方のパターンを検索
    gender_files_raw = glob.glob(f'{data_dir}/sentinel_weekly_gender_*_raw.csv')
    gender_files_normal = glob.glob(f'{data_dir}/sentinel_weekly_gender_*.csv')
    # 重複を除去して結合
    gender_files = list(set(gender_files_raw + gender_files_normal))
    gender_files.sort()  # ソートして順序を保証
    
    processed_data = []
    diseases_found = set()
    
    print(f"Processing {len(gender_files)} gender files...")
    
    for i, filepath in enumerate(gender_files):
        if i % 100 == 0:
            print(f"Processed {i}/{len(gender_files)} files...")
            
        metadata = parse_filename(filepath)
        if not metadata:
            continue
            
        headers, data_rows, period_info = read_sentinel_csv(filepath)
        if not headers or not data_rows:
            continue
            
        # 合算データの場合は警告を出してスキップ
        if period_info.get('is_aggregated', False):
            print(f"警告: {os.path.basename(filepath)} は合算データです（開始週: {period_info['start_week']}, 終了週: {period_info['end_week']}）。スキップします。")
            continue
        
        # データ構造を確認
        # 期待される列: ["疾病名", "男性", "女性", "男女合計", "定点数"]
        if len(headers) < 4:
            continue
        
        # 異常に大きい値の検出（前週の3倍以上など）
        # インフルエンザの値が異常に大きい場合は警告
        influenza_value = None
        for row in data_rows:
            if len(row) >= 4 and 'インフルエンザ' in row[0] and '入院' not in row[0]:
                try:
                    influenza_value = int(row[3] or 0)
                    # 異常に大きい値（例：10,000件以上）の場合は警告
                    if influenza_value > 10000:
                        print(f"警告: {os.path.basename(filepath)} のインフルエンザ値が異常に大きいです（{influenza_value:,}件）。合算データの可能性があります。スキップします。")
                        break
                except (ValueError, IndexError):
                    pass
        
        # 異常値が検出された場合はスキップ
        if influenza_value and influenza_value > 10000:
            continue
            
        for row in data_rows:
            if len(row) < 4:
                continue
                
            disease_name = row[0].strip()
            if not disease_name or disease_name == '疾病名':
                continue
            
            # 除外対象の疾病はスキップ
            if disease_name in EXCLUDED_DISEASES:
                continue
                
            diseases_found.add(disease_name)
            
            try:
                male_count = int(row[1] or 0)
                female_count = int(row[2] or 0)
                total_count = int(row[3] or 0)
                sentinel_points = int(row[4] or 0) if len(row) > 4 else 0
                
                # 疫学週から日付を計算
                week_date = f"{metadata['year']}-W{metadata['week']:02d}"
                
                processed_data.append({
                    'disease_name': disease_name,
                    'year': metadata['year'],
                    'week': metadata['week'],
                    'week_date': week_date,
                    'male_count': male_count,
                    'female_count': female_count,
                    'total_count': total_count,
                    'sentinel_points': sentinel_points,
                    'data_type': 'gender'
                })
                
            except (ValueError, IndexError):
                continue
    
    print(f"Found {len(diseases_found)} unique diseases")
    print(f"Processed {len(processed_data)} records")
    
    return processed_data, list(diseases_found)

def create_disease_summary(processed_data):
    """
    疾病別のサマリー統計を作成
    """
    disease_stats = defaultdict(lambda: {
        'total_reports': 0,
        'total_cases': 0,
        'years_active': set(),
        'peak_year': None,
        'peak_count': 0,
        'avg_weekly_cases': 0
    })
    
    # 年別集計
    yearly_disease_stats = defaultdict(lambda: defaultdict(int))
    
    for record in processed_data:
        disease = record['disease_name']
        year = record['year']
        count = record['total_count']
        
        disease_stats[disease]['total_reports'] += 1
        disease_stats[disease]['total_cases'] += count
        disease_stats[disease]['years_active'].add(year)
        
        yearly_disease_stats[disease][year] += count
        
        # ピーク年の更新
        if yearly_disease_stats[disease][year] > disease_stats[disease]['peak_count']:
            disease_stats[disease]['peak_count'] = yearly_disease_stats[disease][year]
            disease_stats[disease]['peak_year'] = year
    
    # 平均週間症例数を計算
    for disease in disease_stats:
        stats = disease_stats[disease]
        if stats['total_reports'] > 0:
            stats['avg_weekly_cases'] = stats['total_cases'] / stats['total_reports']
        stats['years_active'] = sorted(list(stats['years_active']))
        stats['years_span'] = len(stats['years_active'])
    
    # 辞書型に変換（JSONシリアライズ可能）
    return {disease: dict(stats) for disease, stats in disease_stats.items()}

def main():
    """
    メイン処理
    """
    print("Starting Sentinel surveillance data processing...")
    
    # 出力ディレクトリの作成
    output_dir = 'processed_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # 男女別データの処理
    print("Processing gender-based data...")
    processed_data, diseases = process_gender_data()
    
    if not processed_data:
        print("No data processed. Exiting.")
        return
    
    # 疾病別サマリーの作成
    print("Creating disease summaries...")
    disease_summary = create_disease_summary(processed_data)
    
    # 主要疾患のフィルタリング
    major_diseases = [
        'インフルエンザ',
        '感染性胃腸炎',
        'RSウイルス感染症',
        '手足口病',
        'Ａ群溶血性レンサ球菌咽頭炎',
        '水痘',
        'ヘルパンギーナ',
        '突発性発しん',
        '流行性耳下腺炎',
        '咽頭結膜熱',
        '川崎病',
        '新型コロナウイルス感染症（COVID-19）'
    ]
    
    # 実際に存在する疾患のみをフィルタ
    available_major_diseases = [d for d in major_diseases if d in diseases]
    
    # 結果の保存
    print("Saving processed data...")
    
    # 全データ（主要疾患のみ）
    major_disease_data = [
        record for record in processed_data 
        if record['disease_name'] in available_major_diseases
    ]
    
    # CSVファイルとして保存
    with open(f'{output_dir}/sentinel_diseases_data.csv', 'w', encoding='utf-8', newline='') as f:
        if major_disease_data:
            writer = csv.DictWriter(f, fieldnames=major_disease_data[0].keys())
            writer.writeheader()
            writer.writerows(major_disease_data)
    
    # 疾病リストの保存
    with open(f'{output_dir}/sentinel_disease_list.json', 'w', encoding='utf-8') as f:
        json.dump(available_major_diseases, f, ensure_ascii=False, indent=2)
    
    # 疾病別サマリーの保存（主要疾患のみ）
    major_disease_summary = {
        disease: disease_summary[disease] 
        for disease in available_major_diseases 
        if disease in disease_summary
    }
    
    with open(f'{output_dir}/sentinel_summary_statistics.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_records': len(major_disease_data),
            'total_diseases': len(available_major_diseases),
            'available_diseases': available_major_diseases,
            'date_range': {
                'start_year': min(record['year'] for record in major_disease_data) if major_disease_data else None,
                'end_year': max(record['year'] for record in major_disease_data) if major_disease_data else None
            },
            'disease_statistics': major_disease_summary
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Processing complete!")
    print(f"- Total records processed: {len(processed_data)}")
    print(f"- Major disease records: {len(major_disease_data)}")
    print(f"- Available major diseases: {len(available_major_diseases)}")
    print(f"- All unique diseases found: {len(diseases)}")
    
    # 発見された疾患の一覧表示
    print("\nAvailable major diseases:")
    for disease in available_major_diseases:
        stats = disease_summary.get(disease, {})
        print(f"  - {disease}: {stats.get('total_cases', 0)} cases, {stats.get('years_span', 0)} years")

if __name__ == "__main__":
    main()