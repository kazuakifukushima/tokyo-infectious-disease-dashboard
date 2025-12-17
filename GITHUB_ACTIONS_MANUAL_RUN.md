# GitHub Actions 手動実行ガイド

## 方法1: GitHub Web UIから手動実行（推奨）

1. GitHubリポジトリ（`kazuakifukushima/tokyo-infectious-disease-dashboard`）にアクセス
2. 「Actions」タブをクリック
3. 左側のメニューから「データ自動更新」ワークフローを選択
4. 右上の「Run workflow」ボタンをクリック
5. ブランチを選択（通常は`main`）
6. 「Run workflow」ボタンをクリックして実行

## 方法2: GitHub CLIを使用（認証が必要）

### 認証手順
```bash
gh auth login
```

### ワークフロー一覧の確認
```bash
cd /Users/fukushimakazuaki/cursor/idsc_dashboard
gh workflow list
```

### 手動実行
```bash
gh workflow run "データ自動更新.yml"
```

### 実行状況の確認
```bash
gh run list --workflow="データ自動更新.yml"
```

### 最新の実行ログを確認
```bash
gh run watch
```

## 実行結果の確認

ワークフローが正常に完了すると、以下のファイルが更新されます：
- `backend/processed_data/infectious_diseases_data.csv`
- `backend/processed_data/summary_statistics.json`
- `data/sentinel_diseases_data.csv`
- `data/sentinel_summary_statistics.json`
- `public/data/` ディレクトリ内のファイル（Vercel用）

## トラブルシューティング

### レート制限エラー
GitHub APIのレート制限に達した場合、raw URLから直接取得する方式が自動的に使用されます。

### データが更新されない
- リポジトリ `https://github.com/kambarakun/fetch-tokyo-idsc` に新しいデータが存在するか確認
- ワークフローのログを確認してエラーがないかチェック

