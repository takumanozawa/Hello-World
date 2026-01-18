# クイックスタートガイド

ICT施工Stage2管理システムを**5分で起動**する手順です。

## 📋 前提条件

以下がインストールされていること:
- ✅ Docker Desktop (Windows/Mac) または Docker Engine (Linux)
- ✅ Git

**動作確認済み環境:**
- Docker 24.0+
- Docker Compose v2.0+
- メモリ 8GB以上推奨

---

## 🚀 3ステップで起動

### Step 1: リポジトリのクローン

```bash
git clone https://github.com/takumanozawa/Hello-World.git
cd Hello-World
```

### Step 2: 簡単デプロイスクリプト実行

```bash
# ローカル環境にデプロイ
./scripts/deploy.sh local
```

このスクリプトが自動で以下を実行します:
1. 環境変数ファイル(.env)の作成
2. Dockerコンテナのビルド
3. データベースの起動
4. マイグレーション実行
5. すべてのサービスの起動

### Step 3: ブラウザでアクセス

起動完了後、以下のURLにアクセス:

- **🌐 フロントエンド**: http://localhost:3000
- **🔧 バックエンドAPI**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs

---

## 🎯 初回起動時の確認事項

### 1. サービスの状態確認

```bash
docker-compose ps
```

すべてのサービスが `Up` になっていればOK:
```
NAME                   STATUS
ict_backend            Up
ict_celery_beat        Up
ict_celery_worker      Up
ict_frontend           Up
ict_minio              Up
ict_postgres           Up
ict_redis              Up
```

### 2. ログの確認

```bash
# すべてのログ
docker-compose logs -f

# 特定のサービス
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. データベースの確認

```bash
# PostgreSQLに接続
docker-compose exec postgres psql -U ict_user -d ict_construction

# テーブル一覧
\dt

# 終了
\q
```

---

## 📱 画面の使い方

### ダッシュボード
- 現場、車両、運搬回数などの統計を表示
- アラートの確認
- リアルタイムマップ（実装予定）

### 現場管理
- 現場の追加・編集・削除
- 工程タスクの管理
- 進捗状況の確認

### 車両追跡
- 車両の位置をリアルタイム表示（実装予定）
- GPS軌跡の確認

### シミュレーション
- サイクルタイムのシミュレーション
- ボトルネック分析
- 改善提案の表示

---

## 🛠️ よくある操作

### サービスの停止

```bash
docker-compose stop
```

### サービスの再起動

```bash
docker-compose restart
```

### データベースのリセット

```bash
# すべてのコンテナとデータを削除
docker-compose down -v

# 再度デプロイ
./scripts/deploy.sh local
```

### バックアップの作成

```bash
./scripts/backup.sh
```

バックアップは `backups/` ディレクトリに保存されます。

---

## 🔧 トラブルシューティング

### ポートが既に使用されている

**エラー:**
```
Error: port 3000 is already allocated
```

**解決方法:**
1. 既存のサービスを停止
2. または、`docker-compose.yml` のポート番号を変更

```yaml
# 例: フロントエンドのポートを3001に変更
frontend:
  ports:
    - "3001:3000"
```

### Dockerが起動しない

**解決方法:**
```bash
# Dockerデーモンの再起動
sudo systemctl restart docker  # Linux
# または Docker Desktopを再起動 (Windows/Mac)
```

### データベース接続エラー

**解決方法:**
```bash
# PostgreSQLコンテナのログを確認
docker-compose logs postgres

# コンテナを再起動
docker-compose restart postgres
```

### フロントエンドが表示されない

**解決方法:**
```bash
# フロントエンドコンテナのログを確認
docker-compose logs frontend

# ブラウザのキャッシュをクリア
# Ctrl + Shift + R (Windows/Linux)
# Cmd + Shift + R (Mac)
```

---

## 📚 次のステップ

### 開発を始める

詳細な開発ガイドを参照:
```bash
cat docs/DEVELOPMENT_GUIDE.md
```

### システム設計を理解する

```bash
cat docs/SYSTEM_DESIGN.md
cat docs/DATABASE_SCHEMA.md
```

### 本番環境にデプロイする

```bash
# デプロイガイドを参照
cat docs/DEPLOYMENT_GUIDE.md

# 本番環境へデプロイ（要sudo）
sudo ./scripts/deploy.sh production
```

---

## 💡 便利なコマンド集

```bash
# ヘルスチェック
curl http://localhost:8000/health

# API仕様の確認
open http://localhost:8000/docs  # Mac
xdg-open http://localhost:8000/docs  # Linux

# データベースバックアップ
./scripts/backup.sh

# ログのリアルタイム監視
docker-compose logs -f --tail=100

# リソース使用状況の確認
docker stats

# 未使用のDockerリソースを削除
docker system prune -a

# 特定のコンテナでコマンド実行
docker-compose exec backend bash
docker-compose exec postgres psql -U ict_user -d ict_construction
```

---

## 🆘 サポート

### ドキュメント
- [README.md](README.md) - プロジェクト概要
- [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) - システム設計
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - DB設計
- [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) - 開発ガイド
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - デプロイガイド
- [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) - 実装状況

### 問題が解決しない場合

1. ログを確認: `docker-compose logs`
2. Githubのissuesで検索
3. 新しいissueを作成

---

**これで起動完了です！**

システムを使い始める準備が整いました。
まずはダッシュボード (http://localhost:3000) にアクセスしてみましょう！
