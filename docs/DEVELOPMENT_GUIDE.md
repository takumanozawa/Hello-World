# 開発ガイド

## 開発環境のセットアップ

### 必要な環境

- Docker & Docker Compose
- Node.js 18+ & pnpm
- Python 3.11+ & Poetry
- Git

### 初期セットアップ

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd Hello-World

# 2. バックエンドの依存関係インストール
cd backend
poetry install
cd ..

# 3. フロントエンドの依存関係インストール
cd frontend
pnpm install
cd ..

# 4. 環境変数の設定
cp backend/.env.example backend/.env
# .envファイルを編集して必要な設定を行う

# 5. Docker環境の起動
docker-compose up -d postgres redis minio

# 6. データベースマイグレーション
cd backend
poetry run alembic upgrade head
cd ..
```

### 開発サーバーの起動

#### バックエンド

```bash
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

アクセス: http://localhost:8000
APIドキュメント: http://localhost:8000/docs

#### フロントエンド

```bash
cd frontend
pnpm dev
```

アクセス: http://localhost:3000

### Docker Composeで全体を起動

```bash
docker-compose up
```

---

## プロジェクト構造

### バックエンド (backend/)

```
backend/
├── app/
│   ├── api/v1/              # APIエンドポイント
│   │   ├── endpoints/       # 各エンドポイントの実装
│   │   └── deps/            # 依存関係（認証など）
│   ├── core/                # コア設定
│   │   ├── config.py        # アプリケーション設定
│   │   └── security.py      # セキュリティ（JWT、パスワード）
│   ├── db/                  # データベース設定
│   │   └── base.py          # SQLAlchemyエンジン、セッション
│   ├── models/              # SQLAlchemyモデル
│   │   ├── site.py          # 現場関連モデル
│   │   ├── vehicle.py       # 車両・リソース関連モデル
│   │   ├── alert.py         # アラート・通知関連モデル
│   │   ├── simulation.py    # シミュレーション関連モデル
│   │   └── user.py          # ユーザー管理モデル
│   ├── schemas/             # Pydanticスキーマ
│   │   └── site.py          # 現場関連スキーマ
│   ├── services/            # ビジネスロジック
│   │   ├── gps_service.py   # GPS端末連携
│   │   ├── cycle_service.py # サイクルタイム計測
│   │   └── simulation_service.py # シミュレーション
│   ├── utils/               # ユーティリティ
│   └── main.py              # FastAPIアプリケーション
├── alembic/                 # マイグレーション
│   ├── versions/            # マイグレーションスクリプト
│   └── env.py               # Alembic設定
├── tests/                   # テストコード
├── scripts/                 # 運用スクリプト
├── pyproject.toml           # Poetry設定
├── alembic.ini              # Alembic設定
└── Dockerfile
```

### フロントエンド (frontend/)

```
frontend/
├── src/
│   ├── components/          # Reactコンポーネント
│   │   ├── common/          # 共通コンポーネント（Layout等）
│   │   ├── dashboard/       # ダッシュボード用コンポーネント
│   │   ├── gantt/           # ガントチャート
│   │   ├── map/             # 地図表示
│   │   └── reports/         # レポート
│   ├── pages/               # ページコンポーネント
│   │   ├── Dashboard.tsx    # ダッシュボード
│   │   ├── SiteList.tsx     # 現場一覧
│   │   ├── VehicleTracking.tsx # 車両追跡
│   │   ├── Schedule.tsx     # 工程管理
│   │   ├── Reports.tsx      # レポート
│   │   └── Simulation.tsx   # シミュレーション
│   ├── services/            # API通信
│   ├── store/               # Redux store
│   ├── types/               # TypeScript型定義
│   ├── utils/               # ユーティリティ
│   ├── theme.ts             # Material-UIテーマ
│   ├── App.tsx              # ルートコンポーネント
│   └── main.tsx             # エントリーポイント
├── public/                  # 静的ファイル
├── package.json             # pnpm設定
├── tsconfig.json            # TypeScript設定
├── vite.config.ts           # Vite設定
└── Dockerfile
```

---

## 開発フロー

### 1. 新機能の開発

```bash
# ブランチを作成
git checkout -b feature/新機能名

# 開発を進める
# ...

# コミット
git add .
git commit -m "Add: 新機能の説明"

# プッシュ
git push origin feature/新機能名
```

### 2. データベースマイグレーション

```bash
# マイグレーションファイルを自動生成
cd backend
poetry run alembic revision --autogenerate -m "マイグレーションの説明"

# マイグレーションを適用
poetry run alembic upgrade head

# ロールバック（1つ前に戻す）
poetry run alembic downgrade -1
```

### 3. テストの実行

```bash
# バックエンド
cd backend
poetry run pytest

# フロントエンド
cd frontend
pnpm test
```

### 4. コード品質チェック

```bash
# バックエンド
cd backend
poetry run ruff check .
poetry run black --check .
poetry run mypy .

# フロントエンド
cd frontend
pnpm lint
pnpm format
```

---

## 主要な開発タスク

### APIエンドポイントの追加

1. **モデルの定義** (`backend/app/models/`)
2. **スキーマの定義** (`backend/app/schemas/`)
3. **サービスロジック** (`backend/app/services/`)
4. **エンドポイント実装** (`backend/app/api/v1/endpoints/`)
5. **ルーターへの登録** (`backend/app/api/v1/api.py`)

### Reactコンポーネントの追加

1. **型定義** (`frontend/src/types/`)
2. **APIサービス** (`frontend/src/services/`)
3. **Redux slice** (`frontend/src/store/slices/`)
4. **コンポーネント実装** (`frontend/src/components/` または `frontend/src/pages/`)

---

## デバッグ

### バックエンドのデバッグ

```python
# ログ出力
import logging
logger = logging.getLogger(__name__)
logger.debug("デバッグメッセージ")
logger.info("情報メッセージ")
logger.error("エラーメッセージ")

# ブレークポイント（VSCode）
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### フロントエンドのデバッグ

- ブラウザの開発者ツール（F12）
- React Developer Tools（Chrome拡張）
- Redux DevTools（Chrome拡張）

---

## トラブルシューティング

### Docker関連

```bash
# コンテナのログを確認
docker-compose logs backend
docker-compose logs frontend

# コンテナを再起動
docker-compose restart backend

# すべてクリーンアップ
docker-compose down -v
docker-compose up --build
```

### データベース関連

```bash
# データベースに直接接続
docker exec -it ict_postgres psql -U ict_user -d ict_construction

# テーブル一覧
\dt

# データベースリセット
docker-compose down -v
docker-compose up -d postgres
cd backend && poetry run alembic upgrade head
```

---

## ベストプラクティス

### バックエンド

1. **非同期処理を活用** - `async/await`を使用
2. **型ヒントを徹底** - Python 3.11+の型ヒント機能を活用
3. **エラーハンドリング** - 適切な例外処理とHTTPステータスコード
4. **バリデーション** - Pydanticスキーマで入力検証
5. **ドキュメント** - Docstring（Google形式）を記述

### フロントエンド

1. **コンポーネントの分割** - 単一責任の原則
2. **TypeScriptの型安全性** - `any`の使用を避ける
3. **状態管理の最適化** - 必要最小限の状態のみをReduxに
4. **アクセシビリティ** - ARIA属性を適切に使用
5. **パフォーマンス** - React.memoとuseMemoを適切に使用

---

## リリース手順

### 本番デプロイ

1. **環境変数の設定** - 本番用の`.env`ファイルを作成
2. **ビルド** - `docker-compose -f docker-compose.prod.yml build`
3. **デプロイ** - `docker-compose -f docker-compose.prod.yml up -d`
4. **マイグレーション** - `poetry run alembic upgrade head`
5. **ヘルスチェック** - `/health`エンドポイントを確認

---

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [TimescaleDB Documentation](https://docs.timescale.com/)

---

**最終更新**: 2026-01-18
