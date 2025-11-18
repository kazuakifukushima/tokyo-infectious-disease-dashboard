#!/usr/bin/env python3
"""
GitHubリポジトリからCSVファイルを取得するモジュール
https://github.com/kambarakun/fetch-tokyo-idsc-github-actions からデータを取得
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
    
    def __init__(self, repo_owner: str = "kambarakun", repo_name: str = "fetch-tokyo-idsc-github-actions"):
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
    
    def download_file(self, download_url: str, save_path: str) -> bool:
        """ファイルをダウンロードして保存"""
        try:
            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            logger.info(f"ファイルをダウンロードしました: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"ファイルのダウンロードに失敗しました {download_url}: {str(e)}")
            return False
    
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
        
        Args:
            days: 何日前までの変更を取得するか
            max_files: 最大取得ファイル数
        
        Returns:
            定点把握疾患CSVファイル情報のリスト
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
            # フォールバック: 最初のページのみ取得
            return self.list_sentinel_csv_files("data/raw")[:max_files]
    
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

