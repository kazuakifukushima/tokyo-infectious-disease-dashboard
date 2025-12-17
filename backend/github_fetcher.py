#!/usr/bin/env python3
"""
GitHubリポジトリからCSVファイルを取得するモジュール
https://github.com/kambarakun/fetch-tokyo-idsc からデータを取得
レート制限回避のため、raw URLから直接取得する方式も実装
"""

import os
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import tempfile
import shutil

logger = logging.getLogger(__name__)


class GitHubFetcher:
    """GitHubリポジトリからCSVファイルを取得するクラス"""
    
    def __init__(self, repo_owner: str = "kambarakun", repo_name: str = "fetch-tokyo-idsc"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.raw_base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main"
        
    def get_latest_commit_sha(self, branch: str = "main") -> Optional[str]:
        """最新のコミットSHAを取得"""
        try:
            url = f"{self.base_url}/commits/{branch}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            commit_data = response.json()
            return commit_data.get("sha")
        except Exception as e:
            logger.error(f"最新コミットの取得に失敗しました: {str(e)}")
            return None
    
    def list_csv_files(self, path: str = "data/raw") -> List[Dict]:
        """指定されたパス内のCSVファイル一覧を取得（ページネーション対応）"""
        try:
            csv_files = []
            page = 1
            per_page = 100  # GitHub APIの最大値
            
            while True:
                url = f"{self.base_url}/contents/{path}"
                params = {"page": page, "per_page": per_page}
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                files = response.json()
                
                # ファイルが空の場合は終了
                if not files:
                    break
                
                for file_info in files:
                    # notifiable_weekly_*.csv または *_raw.csv のパターンにマッチ
                    name = file_info.get("name", "")
                    if (file_info.get("type") == "file" and 
                        name.endswith(".csv") and 
                        (name.startswith("notifiable_weekly_") or name.endswith("_raw.csv"))):
                        csv_files.append({
                            "name": file_info["name"],
                            "path": file_info["path"],
                            "sha": file_info["sha"],
                            "size": file_info["size"],
                            "download_url": file_info["download_url"]
                        })
                
                # 100件未満の場合は最後のページ
                if len(files) < per_page:
                    break
                
                page += 1
            
            logger.info(f"CSVファイルを {len(csv_files)} 件見つけました")
            return csv_files
            
        except Exception as e:
            logger.error(f"CSVファイル一覧の取得に失敗しました: {str(e)}")
            return []
    
    def list_sentinel_csv_files(self, path: str = "data/raw") -> List[Dict]:
        """定点把握疾患のCSVファイル一覧を取得（ページネーション対応）"""
        try:
            csv_files = []
            page = 1
            per_page = 100  # GitHub APIの最大値
            
            while True:
                url = f"{self.base_url}/contents/{path}"
                params = {"page": page, "per_page": per_page}
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                files = response.json()
                
                # ファイルが空の場合は終了
                if not files:
                    break
                
                for file_info in files:
                    # sentinel_weekly_*.csv のパターンにマッチ
                    name = file_info.get("name", "")
                    if (file_info.get("type") == "file" and 
                        name.endswith(".csv") and 
                        name.startswith("sentinel_weekly_")):
                        csv_files.append({
                            "name": file_info["name"],
                            "path": file_info["path"],
                            "sha": file_info["sha"],
                            "size": file_info["size"],
                            "download_url": file_info["download_url"]
                        })
                
                # 100件未満の場合は最後のページ
                if len(files) < per_page:
                    break
                
                page += 1
            
            logger.info(f"定点把握疾患CSVファイルを {len(csv_files)} 件見つけました")
            return csv_files
            
        except Exception as e:
            logger.error(f"定点把握疾患CSVファイル一覧の取得に失敗しました: {str(e)}")
            return []
    
    def download_file(self, download_url: str, save_path: str = None) -> Optional[bytes]:
        """
        ファイルをダウンロード
        
        Args:
            download_url: ダウンロードURL
            save_path: 保存先パス（Noneの場合はメモリ上のみ保持）
        
        Returns:
            save_pathが指定された場合: 成功時True、失敗時False
            save_pathがNoneの場合: ファイルコンテンツ（bytes）、失敗時None
        """
        try:
            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()
            
            content = response.content
            
            if save_path:
                # ファイルに保存
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(content)
                logger.info(f"ファイルをダウンロードしました: {save_path}")
                return True
            else:
                # メモリ上のみ保持
                logger.debug(f"ファイルコンテンツを取得しました: {download_url}")
                return content
            
        except Exception as e:
            logger.error(f"ファイルのダウンロードに失敗しました {download_url}: {str(e)}")
            return None if save_path is None else False
    
    def get_file_content(self, path: str) -> Optional[str]:
        """ファイルの内容を取得（テキストファイル用）"""
        try:
            url = f"{self.raw_base_url}/{path}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"ファイル内容の取得に失敗しました {path}: {str(e)}")
            return None
    
    def get_recent_csv_files(self, days: int = 30, max_files: int = 100) -> List[Dict]:
        """
        最近変更されたCSVファイルを取得（レート制限回避のため）
        
        Args:
            days: 何日前までの変更を取得するか
            max_files: 最大取得ファイル数
        
        Returns:
            CSVファイル情報のリスト
        """
        try:
            # 最新のコミットを取得
            commits_url = f"{self.base_url}/commits"
            params = {"per_page": 10}  # 最新10コミットを取得
            response = requests.get(commits_url, params=params, timeout=30)
            response.raise_for_status()
            commits = response.json()
            
            if not commits:
                logger.warning("コミットが見つかりませんでした")
                return []
            
            csv_files = []
            seen_files = set()
            
            # 各コミットから変更されたファイルを取得
            for commit in commits[:5]:  # 最新5コミットまで
                commit_sha = commit["sha"]
                commit_url = f"{self.base_url}/commits/{commit_sha}"
                commit_response = requests.get(commit_url, timeout=30)
                
                if commit_response.status_code != 200:
                    continue
                
                commit_data = commit_response.json()
                files = commit_data.get("files", [])
                
                for file_info in files:
                    filename = file_info.get("filename", "")
                    # CSVファイルで、data/raw内のファイルのみ
                    if (filename.startswith("data/raw/") and 
                        filename.endswith(".csv") and 
                        "notifiable_weekly_" in filename and
                        filename not in seen_files):
                        
                        file_name = os.path.basename(filename)
                        csv_files.append({
                            "name": file_name,
                            "path": filename,
                            "sha": file_info.get("sha"),
                            "size": file_info.get("changes", 0),
                            "download_url": f"{self.raw_base_url}/{filename}"
                        })
                        seen_files.add(filename)
                        
                        if len(csv_files) >= max_files:
                            break
                
                if len(csv_files) >= max_files:
                    break
            
            logger.info(f"最近のCSVファイルを {len(csv_files)} 件見つけました")
            return csv_files
            
        except Exception as e:
            logger.error(f"最近のCSVファイル取得に失敗しました: {str(e)}")
            # フォールバック: 最初のページのみ取得
            return self.list_csv_files("data/raw")[:max_files]
    
    def get_recent_sentinel_csv_files(self, days: int = 30, max_files: int = 100) -> List[Dict]:
        """
        最近変更された定点把握疾患CSVファイルを取得（レート制限回避のため）
        raw URLから直接取得する方式も試行
        
        Args:
            days: 何日前までの変更を取得するか
            max_files: 最大取得ファイル数
        
        Returns:
            定点把握疾患CSVファイル情報のリスト
        """
        # まず、raw URLから直接取得を試行（レート制限回避）
        csv_files = self._get_sentinel_files_via_raw_url(max_files)
        if csv_files:
            logger.info(f"raw URLから {len(csv_files)} 件の定点把握疾患CSVファイルを取得しました")
            return csv_files
        
        # フォールバック: GitHub APIを使用
        try:
            # 最新のコミットを取得
            commits_url = f"{self.base_url}/commits"
            params = {"per_page": 10}  # 最新10コミットを取得
            response = requests.get(commits_url, params=params, timeout=30)
            response.raise_for_status()
            commits = response.json()
            
            if not commits:
                logger.warning("コミットが見つかりませんでした")
                return []
            
            csv_files = []
            seen_files = set()
            
            # 各コミットから変更されたファイルを取得
            for commit in commits[:5]:  # 最新5コミットまで
                commit_sha = commit["sha"]
                commit_url = f"{self.base_url}/commits/{commit_sha}"
                commit_response = requests.get(commit_url, timeout=30)
                
                if commit_response.status_code != 200:
                    continue
                
                commit_data = commit_response.json()
                files = commit_data.get("files", [])
                
                for file_info in files:
                    filename = file_info.get("filename", "")
                    # CSVファイルで、data/raw内の定点把握疾患ファイルのみ
                    if (filename.startswith("data/raw/") and 
                        filename.endswith(".csv") and 
                        "sentinel_weekly_" in filename and
                        filename not in seen_files):
                        
                        file_name = os.path.basename(filename)
                        csv_files.append({
                            "name": file_name,
                            "path": filename,
                            "sha": file_info.get("sha"),
                            "size": file_info.get("changes", 0),
                            "download_url": f"{self.raw_base_url}/{filename}"
                        })
                        seen_files.add(filename)
                        
                        if len(csv_files) >= max_files:
                            break
                
                if len(csv_files) >= max_files:
                    break
            
            logger.info(f"最近の定点把握疾患CSVファイルを {len(csv_files)} 件見つけました")
            return csv_files
            
        except Exception as e:
            logger.error(f"最近の定点把握疾患CSVファイル取得に失敗しました: {str(e)}")
            # フォールバック: raw URLから直接取得を再試行
            return self._get_sentinel_files_via_raw_url(max_files)
    
    def _get_sentinel_files_via_raw_url(self, max_files: int = 100) -> List[Dict]:
        """
        raw URLから直接定点把握疾患CSVファイルを取得（レート制限回避）
        最新の週から順に試行
        """
        from datetime import datetime, timedelta
        
        csv_files = []
        current_date = datetime.now()
        current_year = current_date.year
        
        # 現在の週番号を計算（ISO週番号を使用）
        # より正確な週番号計算
        jan1 = datetime(current_year, 1, 1)
        days_since_jan1 = (current_date - jan1).days
        # ISO週番号を計算（月曜日を週の始まりとする）
        current_week = (days_since_jan1 // 7) + 1
        
        # 最新の週から遡って取得（最大52週分 + 最新の数週間を多めにチェック）
        weeks_to_check = []
        # 現在の年: 最新の週から遡る（最大60週分チェック）
        for week in range(max(1, current_week - 60), current_week + 5):
            weeks_to_check.append((current_year, week))
        
        # 前年もチェック（最新の数週間）
        if current_year > 2000:
            for week in range(max(1, 52 - 15), 53):
                weeks_to_check.append((current_year - 1, week))
        
        logger.info(f"raw URLから定点把握疾患ファイルを検索中: {len(weeks_to_check)} 週分")
        
        # 複数のリポジトリ名を試す
        repo_names = [self.repo_name, "fetch-tokyo-idsc-github-actions"]
        
        for repo_name in repo_names:
            raw_base_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{repo_name}/main"
            
            for year, week in weeks_to_check:
                if len(csv_files) >= max_files:
                    break
                
                # 複数のファイル名パターンを試す
                # パターン1: sentinel_weekly_gender_2025_25.csv
                # パターン2: sentinel_weekly_gender_2025_25_20250703_031821_raw.csv
                # パターン3: sentinel_weekly_gender_2025_25_YYYYMMDD_HHMMSS_raw.csv (最近の日付パターン)
                filenames = [
                    f"sentinel_weekly_gender_{year}_{week:02d}.csv",
                    f"sentinel_weekly_gender_{year}_{week}.csv",
                ]
                
                # 最近の日付パターンも追加（過去30日間）
                for days_ago in range(0, 30, 7):  # 7日ごとにチェック
                    check_date = current_date - timedelta(days=days_ago)
                    filenames.append(f"sentinel_weekly_gender_{year}_{week}_{check_date.strftime('%Y%m%d')}_000000_raw.csv")
                
                for filename in filenames:
                    raw_url = f"{raw_base_url}/data/raw/{filename}"
                    try:
                        # HEADリクエストでファイルの存在確認（GitHub Actions環境ではHEADが失敗する場合があるため、GETも試行）
                        try:
                            response = requests.head(raw_url, timeout=10, allow_redirects=True)
                        except requests.exceptions.RequestException:
                            # HEADが失敗した場合はGETを試行（最初の1バイトのみ取得）
                            response = requests.get(raw_url, timeout=10, allow_redirects=True, stream=True)
                            # ストリームを閉じる
                            response.close()
                            # ステータスコードを確認するため、再度リクエスト（簡易版）
                            response = requests.get(raw_url, timeout=10, allow_redirects=True, headers={'Range': 'bytes=0-0'})
                        
                        if response.status_code == 200 or response.status_code == 206:
                            # ファイルが存在する場合、情報を追加
                            csv_files.append({
                                "name": filename,
                                "path": f"data/raw/{filename}",
                                "sha": None,
                                "size": 0,
                                "download_url": raw_url
                            })
                            logger.info(f"ファイルが見つかりました: {filename} (リポジトリ: {repo_name})")
                            break  # 成功したら次の週へ
                        # 404の場合は次のパターンを試す
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"ファイルチェックエラー {filename}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.debug(f"予期しないエラー {filename}: {str(e)}")
                        continue
            
            # 1つのリポジトリでファイルが見つかったら終了
            if csv_files:
                break
        
        if csv_files:
            logger.info(f"raw URLから {len(csv_files)} 件の定点把握疾患ファイルを発見しました（リポジトリ: {repo_name if 'repo_name' in locals() else 'unknown'}）")
        else:
            logger.warning(f"raw URLから定点把握疾患ファイルが見つかりませんでした（チェックした週数: {len(weeks_to_check)}）")
        return csv_files
    
    def download_new_csv_files(self, local_csv_dir: str, existing_files: Optional[List[str]] = None, use_recent_only: bool = True) -> List[str]:
        """
        新しいCSVファイルをダウンロード
        
        Args:
            local_csv_dir: ローカルのCSV保存ディレクトリ
            existing_files: 既存のファイル名リスト（重複チェック用）
        
        Returns:
            ダウンロードしたファイルのパスリスト
        """
        if existing_files is None:
            existing_files = []
        
        # CSVファイル一覧を取得
        if use_recent_only:
            csv_files = self.get_recent_csv_files()
        else:
            csv_files = self.list_csv_files("data/raw")
        
        if not csv_files:
            logger.warning("ダウンロード可能なCSVファイルが見つかりませんでした")
            return []
        
        downloaded_files = []
        
        for file_info in csv_files:
            filename = file_info["name"]
            
            # 既存ファイルのチェック
            if filename in existing_files:
                logger.debug(f"既存ファイルのためスキップ: {filename}")
                continue
            
            # ファイルをダウンロード
            save_path = os.path.join(local_csv_dir, filename)
            if self.download_file(file_info["download_url"], save_path):
                downloaded_files.append(save_path)
        
        logger.info(f"{len(downloaded_files)} 件の新しいファイルをダウンロードしました")
        return downloaded_files
    
    def check_for_updates(self, last_commit_sha: Optional[str] = None) -> bool:
        """
        リポジトリに更新があるかチェック
        
        Args:
            last_commit_sha: 最後に確認したコミットSHA
        
        Returns:
            更新がある場合True
        """
        current_sha = self.get_latest_commit_sha()
        
        if current_sha is None:
            return False
        
        if last_commit_sha is None:
            return True
        
        return current_sha != last_commit_sha


def get_existing_csv_files(csv_dir: str) -> List[str]:
    """既存のCSVファイル名リストを取得"""
    if not os.path.exists(csv_dir):
        return []
    
    files = [
        f for f in os.listdir(csv_dir)
        if f.endswith('.csv') and f.startswith('notifiable_weekly_')
    ]
    return files


def get_existing_sentinel_csv_files(csv_dir: str) -> List[str]:
    """既存の定点把握疾患CSVファイル名リストを取得"""
    if not os.path.exists(csv_dir):
        return []
    
    files = [
        f for f in os.listdir(csv_dir)
        if f.endswith('.csv') and f.startswith('sentinel_weekly_')
    ]
    return files


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    fetcher = GitHubFetcher()
    
    # 最新コミットSHAを取得
    sha = fetcher.get_latest_commit_sha()
    print(f"最新コミットSHA: {sha}")
    
    # CSVファイル一覧を取得
    csv_files = fetcher.list_csv_files("data/raw")
    print(f"\n見つかったCSVファイル数: {len(csv_files)}")
    
    if csv_files:
        print("\n最初の5ファイル:")
        for file_info in csv_files[:5]:
            print(f"  - {file_info['name']} ({file_info['size']} bytes)")

