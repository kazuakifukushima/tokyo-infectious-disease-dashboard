#!/usr/bin/env python3
"""
GitHub raw URLから直接ファイルをダウンロードするユーティリティ
レート制限を回避するため、ファイル名を推測して直接ダウンロード
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


def get_latest_weeks(year: int, num_weeks: int = 10) -> List[tuple]:
    """最新の週番号を生成"""
    weeks = []
    current_date = datetime.now()
    current_year = current_date.year
    
    # 現在の週番号を計算
    jan1 = datetime(current_year, 1, 1)
    days_since_jan1 = (current_date - jan1).days
    current_week = (days_since_jan1 // 7) + 1
    
    # 指定された年と週の範囲を生成
    if year == current_year:
        # 現在の年の場合、最新の週から遡る
        for week in range(max(1, current_week - num_weeks + 1), current_week + 1):
            weeks.append((year, week))
    else:
        # 過去の年の場合、最後の数週間
        for week in range(max(1, 52 - num_weeks + 1), 53):
            weeks.append((year, week))
    
    return weeks


def download_file_by_name(repo_owner: str, repo_name: str, filename: str, save_path: str) -> bool:
    """ファイル名を指定してraw URLから直接ダウンロード"""
    raw_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/data/raw/{filename}"
    
    try:
        response = requests.get(raw_url, timeout=30, stream=True)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"ファイルをダウンロードしました: {filename}")
            return True
        else:
            logger.debug(f"ファイルが見つかりませんでした: {filename} (HTTP {response.status_code})")
            return False
    except Exception as e:
        logger.debug(f"ダウンロードエラー {filename}: {str(e)}")
        return False


def download_recent_files(
    repo_owner: str = "kambarakun",
    repo_name: str = "fetch-tokyo-idsc-github-actions",
    csv_dir: str = "../csv_list",
    existing_files: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    weeks_per_year: int = 10
) -> List[str]:
    """
    最新のファイルを推測してダウンロード
    
    Args:
        repo_owner: リポジトリオーナー
        repo_name: リポジトリ名
        csv_dir: CSV保存ディレクトリ
        existing_files: 既存ファイルリスト
        years: 対象年（Noneの場合は現在の年と前年）
        weeks_per_year: 各年から取得する週数
    
    Returns:
        ダウンロードしたファイルのパスリスト
    """
    if existing_files is None:
        existing_files = []
    
    if years is None:
        current_year = datetime.now().year
        years = [current_year - 1, current_year]
    
    downloaded_files = []
    
    for year in years:
        weeks = get_latest_weeks(year, weeks_per_year)
        
        for year_num, week_num in weeks:
            # ファイル名を生成（2つの形式を試す）
            filenames = [
                f"notifiable_weekly_{year_num}_{week_num:02d}.csv",
                f"notifiable_weekly_{year_num}_{week_num}_20250703_031821_raw.csv"
            ]
            
            for filename in filenames:
                if filename in existing_files:
                    continue
                
                save_path = os.path.join(csv_dir, filename)
                
                # 既に存在する場合はスキップ
                if os.path.exists(save_path):
                    continue
                
                if download_file_by_name(repo_owner, repo_name, filename, save_path):
                    downloaded_files.append(save_path)
                    break  # 成功したら次の週へ
    
    logger.info(f"{len(downloaded_files)} 件のファイルをダウンロードしました")
    return downloaded_files


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # テスト実行
    files = download_recent_files()
    print(f"ダウンロードしたファイル数: {len(files)}")

