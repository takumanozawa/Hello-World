# ICT施工Stage2管理システム

河道掘削工事向けの統合施工管理システム

## 概要

複数の河道掘削現場を統合管理し、重機・ダンプの稼働状況をリアルタイムに把握、施工データを蓄積・分析して継続的改善を実現するシステムです。

## 主要機能

1. **複数現場の工程統合管理** - ガントチャートによる可視化
2. **車両・重機の位置情報リアルタイム表示** - 地図上での追跡
3. **運搬サイクルタイムの自動計測・分析** - GPS位置データから自動算出
4. **リソース最適配置提案** - AIによる最適化アルゴリズム
5. **事前シミュレーション** - 予実比較による改善
6. **アラート機能** - 遅延、速度超過、滞留検知
7. **日報・週報の自動生成** - Excel形式で出力

## システム構成

```
├── backend/          # FastAPI バックエンド
├── frontend/         # React フロントエンド
├── mobile/           # React Native モバイルアプリ
├── docs/             # ドキュメント
└── docker-compose.yml
```

## 技術スタック

### バックエンド
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL 15 + PostGIS + TimescaleDB
- Redis 7
- Celery

### フロントエンド
- React 18
- TypeScript
- Material-UI (MUI)
- Leaflet (地図)
- Recharts (グラフ)
- DHTMLX Gantt

### モバイル
- React Native
- WatermelonDB

## セットアップ

### 必要な環境
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### 開発環境の起動

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd Hello-World

# 2. Docker環境の起動
docker-compose up -d

# 3. バックエンドのセットアップ
cd backend
poetry install
poetry run alembic upgrade head

# 4. フロントエンドのセットアップ
cd ../frontend
pnpm install

# 5. 開発サーバーの起動
pnpm dev
```

アクセス:
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs

## ドキュメント

- [システム設計書](docs/SYSTEM_DESIGN.md)
- [データベーススキーマ](docs/DATABASE_SCHEMA.md)
- [API仕様書](docs/API_SPECIFICATION.md) ※作成予定
- [開発ガイド](docs/DEVELOPMENT_GUIDE.md) ※作成予定

## ディレクトリ構造

```
backend/
├── app/
│   ├── api/v1/          # APIエンドポイント
│   ├── core/            # コア設定（認証、セキュリティ）
│   ├── db/              # データベース設定
│   ├── models/          # SQLAlchemyモデル
│   ├── schemas/         # Pydanticスキーマ
│   ├── services/        # ビジネスロジック
│   └── utils/           # ユーティリティ
├── tests/               # テストコード
└── scripts/             # 運用スクリプト

frontend/
├── public/              # 静的ファイル
└── src/
    ├── components/      # Reactコンポーネント
    ├── pages/           # ページコンポーネント
    ├── services/        # API通信
    ├── store/           # Redux store
    ├── types/           # TypeScript型定義
    └── utils/           # ユーティリティ

mobile/
└── src/                 # React Nativeアプリ

docs/
├── SYSTEM_DESIGN.md     # システム設計書
├── DATABASE_SCHEMA.md   # DB設計書
└── images/              # 図表
```

## 開発フェーズ

### Phase 1: 基盤構築（完了）
- [x] システム設計
- [x] データベース設計
- [x] プロジェクト構造作成

### Phase 2: コア機能開発（進行中）
- [ ] バックエンドAPI実装
- [ ] GPS端末連携
- [ ] 運行管理・サイクルタイム計測
- [ ] ダッシュボード実装

### Phase 3: 高度機能開発（予定）
- [ ] リソース最適化
- [ ] シミュレーション
- [ ] アラート・通知
- [ ] モバイルアプリ

## ライセンス

Proprietary - All Rights Reserved

## 開発者

ICT Construction Team

---

**最終更新**: 2026-01-18