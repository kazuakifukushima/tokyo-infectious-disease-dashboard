# データ自動更新システム

このディレクトリには、GitHubリポジトリから定期的にデータを取得してダッシュボードを更新するシステムが含まれています。

## 📋 概要

`https://github.com/kambarakun/fetch-tokyo-idsc` から定期的に新しいCSVファイルを取得し、既存のデータベースに統合してダッシュボードを更新します。

## 🔧 コンポーネント

### 1. `github_fetcher.py`
GitHubリポジトリからCSVファイルを取得するモジュール

**主な機能:**
- GitHub APIを使用してCSVファイル一覧を取得
- ファイルをダウンロード
- 更新チェック

**使用方法:**
```python
from github_fetcher import GitHubFetcher

fetcher = GitHubFetcher()
csv_files = fetcher.list_csv_files("data/raw")
downloaded = fetcher.download_new_csv_files("./csv_list", existing_files=[])
```

### 2. `data_updater.py`
データ更新処理を統合するモジュール

**主な機能:**
- GitHubから新しいCSVファイルを取得
- 既存データと統合（重複チェック）
- データ処理と保存
- 更新状態の確認

**使用方法:**
```python
from data_updater import DataUpdater

updater = DataUpdater()
result = updater.update_data()
print(result)
```

### 3. `update_data_scheduled.py`
定期的な実行用スクリプト（cron/GitHub Actions用）

**実行方法:**
```bash
cd backend
python update_data_scheduled.py
```

### 4. `.github/workflows/update-data.yml`
GitHub Actionsワークフロー（毎日自動実行）

## 🚀 使用方法

### 手動実行

```bash
cd backend
python update_data_scheduled.py
```

### API経由での実行

#### 更新状態を確認
```bash
curl http://localhost:8000/update-status
```

#### データを更新（非同期）
```bash
curl -X POST http://localhost:8000/update-data
```

#### データを更新（同期）
```bash
curl -X POST http://localhost:8000/update-data-sync
```

### GitHub Actionsでの自動実行

`.github/workflows/update-data.yml` が設定されている場合、以下のスケジュールで自動実行されます：

- **毎日午前3時（JST）**: 自動的にデータを更新
- **手動実行**: GitHub ActionsのUIから手動で実行可能

## ⚙️ 設定

### リポジトリ設定

`github_fetcher.py` でリポジトリ情報を変更できます：

```python
fetcher = GitHubFetcher(
    repo_owner="kambarakun",
    repo_name="fetch-tokyo-idsc"
)
```

### ディレクトリ設定

`data_updater.py` でディレクトリを変更できます：

```python
updater = DataUpdater(
    csv_dir="../csv_list",
    output_dir="processed_data"
)
```

## 📊 データフロー

1. **GitHubリポジトリから取得**
   - `github_fetcher.py` がGitHub APIを使用してCSVファイル一覧を取得
   - 新しいファイルのみをダウンロード

2. **データ処理**
   - `data_updater.py` が新しいCSVファイルを処理
   - 既存データと統合（重複チェック）

3. **保存**
   - 処理済みデータを `processed_data/` に保存
   - サマリー統計と疾病リストも更新

4. **API更新**
   - バックエンドAPIが新しいデータを読み込み
   - ダッシュボードが自動的に更新

## 🔍 トラブルシューティング

### エラー: "data_updaterモジュールが利用できません"

`requirements.txt` に `requests` が含まれているか確認してください：

```bash
pip install -r requirements.txt
```

### エラー: GitHub APIレート制限

GitHub APIにはレート制限があります。大量のファイルを取得する場合は、時間を空けて実行してください。

### データが更新されない

1. GitHubリポジトリに新しいファイルがあるか確認
2. `update-status` エンドポイントで状態を確認
3. ログファイル（`data_update.log`）を確認

## 📝 ログ

データ更新処理のログは以下の場所に保存されます：

- **ファイル**: `backend/data_update.log`
- **コンソール**: 標準出力

## 🔐 セキュリティ

- GitHub APIは公開リポジトリのため認証不要
- プライベートリポジトリを使用する場合は、GitHubトークンの設定が必要

## 📚 関連ファイル

- `backend/simple_data_processor.py`: CSVファイルの処理ロジック
- `backend/main.py`: FastAPIエンドポイント
- `.github/workflows/update-data.yml`: GitHub Actionsワークフロー

