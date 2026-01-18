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

## 🚀 クイックスタート

**最速5分で起動！**

```bash
# リポジトリをクローン
git clone https://github.com/takumanozawa/Hello-World.git
cd Hello-World

# 自動デプロイスクリプトを実行
./scripts/deploy.sh local
```

詳細は [クイックスタートガイド](QUICKSTART.md) を参照。

### アクセスURL
- 🌐 **フロントエンド**: http://localhost:3000
- 🔧 **バックエンドAPI**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 📦 **MinIO Console**: http://localhost:9001

## 📦 デプロイ

### ローカル環境
```bash
./scripts/deploy.sh local
```

### 本番環境
```bash
sudo ./scripts/deploy.sh production
```

詳細は [デプロイガイド](docs/DEPLOYMENT_GUIDE.md) を参照。

## 🛠️ 運用コマンド

```bash
# サービスの停止
docker-compose stop

# サービスの再起動
docker-compose restart

# バックアップ
./scripts/backup.sh

# ログの確認
docker-compose logs -f
```

## 📚 ドキュメント

### 開始ガイド
- [📖 クイックスタート](QUICKSTART.md) - 5分で起動
- [🚀 デプロイガイド](docs/DEPLOYMENT_GUIDE.md) - ローカル・本番環境へのデプロイ

### 技術ドキュメント
- [🏗️ システム設計書](docs/SYSTEM_DESIGN.md) - 構成図、技術スタック
- [🗄️ データベーススキーマ](docs/DATABASE_SCHEMA.md) - 全テーブル定義、ERD
- [👨‍💻 開発ガイド](docs/DEVELOPMENT_GUIDE.md) - 開発環境、フロー、ベストプラクティス
- [📊 実装状況](docs/IMPLEMENTATION_STATUS.md) - 現在の完成度、次ステップ

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

## 📊 実装状況

**全体進捗**: 約70% (コア機能完成)

### ✅ 完成
- システム設計・ドキュメント (100%)
- バックエンド基盤 (FastAPI, SQLAlchemy, Alembic) (100%)
- データベースモデル (全9ファイル) (100%)
- ビジネスロジック (GPS連携, サイクルタイム計測, シミュレーション) (80%)
- フロントエンド基盤 (React, TypeScript, Material-UI) (100%)
- Docker環境 (100%)
- デプロイスクリプト (100%)

### 🚧 実装予定
- APIエンドポイント (CRUD操作)
- WebSocket (リアルタイム通信)
- 地図表示 (Leaflet)
- ガントチャート (工程管理)
- アラート機能
- レポート生成 (Excel/PDF)
- モバイルアプリ

詳細は [実装状況ドキュメント](docs/IMPLEMENTATION_STATUS.md) を参照。

## ライセンス

Proprietary - All Rights Reserved

## 開発者

ICT Construction Team

---

**最終更新**: 2026-01-18