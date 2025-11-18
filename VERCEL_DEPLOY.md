# Vercelデプロイ手順

## 📋 概要

このダッシュボードはVercelでデプロイ可能です。フロントエンド（Next.js）とバックエンド（FastAPI）を別々にデプロイする必要があります。

## 🚀 デプロイ手順

### 1. フロントエンド（Next.js）のデプロイ

1. **Vercelにログイン**
   - https://vercel.com にアクセス
   - GitHubアカウントでログイン

2. **プロジェクトをインポート**
   - "New Project" をクリック
   - GitHubリポジトリ `kazuakifukushima/tokyo-infectious-disease-dashboard` を選択
   - Framework Preset: **Next.js** を選択（自動検出されるはず）

3. **環境変数の設定**
   - Project Settings → Environment Variables に移動
   - 以下の環境変数を追加：
     ```
     NEXT_PUBLIC_API_URL=https://your-backend-api.vercel.app
     ```
   - または、バックエンドAPIのURLを設定

4. **デプロイ実行**
   - "Deploy" をクリック
   - ビルドが完了するまで待機

### 2. バックエンド（FastAPI）のデプロイ

バックエンドAPIもVercelでデプロイできますが、Pythonランタイムが必要です。

#### オプション1: Vercel Serverless Functionsを使用

1. **バックエンド用の新しいVercelプロジェクトを作成**
2. **`vercel.json` を追加**:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "backend/main.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "backend/main.py"
       }
     ]
   }
   ```

#### オプション2: 別のホスティングサービスを使用

- **Railway**: https://railway.app
- **Render**: https://render.com
- **Fly.io**: https://fly.io

これらのサービスでFastAPIアプリをデプロイし、そのURLを `NEXT_PUBLIC_API_URL` に設定します。

### 3. データファイルの配置

データファイル（`data/` ディレクトリ）はGitHubリポジトリに含まれているため、Vercelのビルド時に自動的に含まれます。

## ⚙️ 環境変数の設定

### フロントエンド（Vercel）

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `NEXT_PUBLIC_API_URL` | バックエンドAPIのURL | `https://your-api.vercel.app` |

### バックエンド（Vercelまたは別サービス）

環境変数は特に必要ありませんが、必要に応じて設定できます。

## 📝 注意事項

1. **バックエンドAPIのURL**: フロントエンドの環境変数でバックエンドAPIのURLを正しく設定してください
2. **CORS設定**: バックエンドAPIの `main.py` でCORS設定が正しく行われていることを確認してください
3. **データファイル**: 大きなデータファイル（CSV）はGitHubリポジトリに含まれているため、初回ビルドに時間がかかる場合があります

## 🔍 トラブルシューティング

### ビルドエラー

- Node.jsのバージョンを確認（`package.json` の `engines.node` を確認）
- 依存関係が正しくインストールされているか確認

### API接続エラー

- 環境変数 `NEXT_PUBLIC_API_URL` が正しく設定されているか確認
- バックエンドAPIが正常に動作しているか確認
- CORS設定を確認

## 📚 参考リンク

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js on Vercel](https://vercel.com/docs/frameworks/nextjs)
- [Deploying Python on Vercel](https://vercel.com/docs/frameworks/python)

