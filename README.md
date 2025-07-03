# 東京都感染症ダッシュボード

東京都の感染症発生動向データを可視化・分析するWebダッシュボードです。

## 🌟 機能

- **概況ダッシュボード**: 全体的な感染症発生動向の把握
- **疾病別分析**: 個別感染症の詳細な時系列分析
- **分類別統計**: 法定感染症分類別の統計情報
- **時系列分析**: 長期的なトレンド分析と予測

## 📊 データ概要

- **データ期間**: 2000年～2025年（25年間）
- **総レコード数**: 97,424件
- **対象感染症**: 93種類
- **データソース**: 東京都感染症週報

### 主要感染症（報告数上位10位）
1. 結核: 62,618件
2. 梅毒: 27,751件
3. 新型コロナウイルス感染症: 14,043件
4. 後天性免疫不全症候群: 10,521件
5. 腸管出血性大腸菌感染症: 8,695件
6. 百日咳: 7,020件
7. 風しん: 6,254件
8. アメーバ赤痢: 3,955件
9. 侵襲性肺炎球菌感染症: 3,374件
10. レジオネラ症: 2,480件

## 🏗️ アーキテクチャ

### フロントエンド
- **Framework**: Next.js 14 + React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Chart.js + react-chartjs-2
- **HTTP Client**: Axios

### バックエンド
- **Framework**: FastAPI
- **Language**: Python 3.13
- **Data Processing**: Pandas, NumPy
- **API Documentation**: OpenAPI/Swagger

### データ処理
- **Format**: CSV (Shift-JIS) → UTF-8
- **Storage**: JSON + CSV
- **Processing**: 週次データの統合・正規化

## 🚀 セットアップ

### 前提条件
- Node.js 18.0.0以上
- Python 3.13以上
- npm または yarn

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd idsc_dashboard
```

### 2. データ処理（初回のみ）
```bash
cd backend
pip3 install fastapi uvicorn python-multipart pydantic python-dotenv
python simple_data_processor.py
```

### 3. バックエンドの起動
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### 4. フロントエンドの起動
```bash
npm install
npm run dev
```

### 5. アプリケーションにアクセス
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📚 使用方法

### 概況ダッシュボード
- 全体的な感染症発生状況を確認
- サマリー統計と主要指標を表示
- 年次推移とトレンドを可視化

### 疾病別分析
1. 分析したい感染症を選択
2. 期間（開始年・終了年）を設定
3. 時系列グラフで発生動向を確認
4. 統計データテーブルで詳細を確認

### 分類別統計
- 感染症法による法定分類別の統計
- 分類別報告数と疾病数の比較
- 各分類の詳細説明

### 時系列分析
- 年別トレンド分析
- 特定年度の詳細分析
- 統計データテーブル

## 🗂️ プロジェクト構造

```
idsc_dashboard/
├── backend/                  # バックエンド
│   ├── main.py              # FastAPI アプリケーション
│   ├── simple_data_processor.py  # データ処理スクリプト
│   ├── processed_data/      # 処理済みデータ
│   └── requirements.txt     # Python依存関係
├── src/                     # フロントエンド
│   ├── app/                 # Next.js App Router
│   ├── components/          # Reactコンポーネント
│   ├── lib/                 # API クライアント
│   └── types/               # TypeScript型定義
├── csv_list/                # 元データCSVファイル
├── package.json             # Node.js依存関係
└── README.md               # このファイル
```

## 🎨 画面構成

### サイドバーナビゲーション
- 📊 概況: 全体サマリー
- 🦠 疾病別分析: 個別疾病の詳細
- 📋 分類別統計: 法定分類別集計
- 📈 時系列分析: 長期トレンド

### メイン画面
- ヘッダー: データ期間とサマリー情報
- コンテンツエリア: 選択した機能に応じた表示
- インタラクティブチャート: クリック・ホバー対応

## 🔧 開発コマンド

```bash
# フロントエンド開発サーバー
npm run dev

# フロントエンドビルド
npm run build

# バックエンド開発サーバー
npm run python-server

# データ再処理
npm run setup-data

# Lint実行
npm run lint
```

## 📄 API エンドポイント

### 基本情報
- `GET /health` - ヘルスチェック
- `GET /summary` - サマリー統計
- `GET /diseases` - 感染症リスト

### データ取得
- `GET /diseases/{disease_name}/timeseries` - 疾病別時系列データ
- `GET /diseases/top` - 上位感染症
- `GET /categories` - 分類別統計
- `GET /yearly-trends` - 年次推移

### 管理
- `GET /reload-data` - データ再読み込み

## 🔐 セキュリティ

- CSVファイルの安全な読み込み（Shift-JIS対応）
- APIのCORS設定
- 入力値の検証とサニタイゼーション

## 🤝 貢献

1. フォークを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 👥 チーム

- **開発**: IDSC Dashboard Team
- **データソース**: 東京都感染症情報センター

---

**注意**: このダッシュボードは教育・研究目的で作成されており、実際の公衆衛生政策の決定には使用しないでください。