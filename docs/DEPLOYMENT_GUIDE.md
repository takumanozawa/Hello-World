# デプロイガイド

## 目次

1. [ローカル開発環境でのデプロイ](#ローカル開発環境でのデプロイ)
2. [本番環境へのデプロイ](#本番環境へのデプロイ)
3. [クラウド環境へのデプロイ](#クラウド環境へのデプロイ)
4. [トラブルシューティング](#トラブルシューティング)

---

## ローカル開発環境でのデプロイ

### 必要な環境

- Docker Desktop（Windows/Mac）または Docker Engine（Linux）
- Docker Compose v2.0以上
- Git
- 8GB以上のメモリ推奨

### Step 1: リポジトリのクローン

```bash
git clone https://github.com/takumanozawa/Hello-World.git
cd Hello-World
```

### Step 2: 環境変数の設定

```bash
# バックエンドの環境変数をコピー
cp backend/.env.example backend/.env

# エディタで編集（必要に応じて）
nano backend/.env
```

**最低限必要な設定:**
```env
# データベース
DATABASE_URL=postgresql+asyncpg://ict_user:ict_password_2026@postgres:5432/ict_construction

# Redis
REDIS_URL=redis://redis:6379/0

# セキュリティ（本番では必ず変更！）
SECRET_KEY=your-secret-key-change-in-production-min-32-chars

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Step 3: Docker Composeで起動

```bash
# すべてのサービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

起動するサービス:
- PostgreSQL (ポート5432)
- Redis (ポート6379)
- MinIO (ポート9000, 9001)
- バックエンドAPI (ポート8000)
- フロントエンド (ポート3000)

### Step 4: データベースマイグレーション

```bash
# バックエンドコンテナに入る
docker-compose exec backend bash

# マイグレーション実行
poetry run alembic upgrade head

# 確認
poetry run alembic current

# コンテナから出る
exit
```

### Step 5: アクセス確認

ブラウザで以下のURLにアクセス:

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (ID: minioadmin / PW: minioadmin123)

### Step 6: 初期データ投入（オプション）

```bash
# バックエンドコンテナに入る
docker-compose exec backend bash

# Pythonシェルを起動
poetry run python

# 以下のコードを実行
```

```python
from app.db.base import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as session:
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            full_name="管理者",
            role="admin",
            is_active="True"
        )
        session.add(admin)
        await session.commit()
        print("管理者ユーザーを作成しました")

asyncio.run(create_admin())
```

### 停止・削除

```bash
# 停止
docker-compose stop

# 停止して削除
docker-compose down

# データボリュームも含めて完全削除
docker-compose down -v
```

---

## 本番環境へのデプロイ

### 前提条件

- Ubuntu 22.04 LTS サーバー
- Docker & Docker Compose インストール済み
- ドメイン取得済み（例: ict-construction.example.com）
- SSL証明書（Let's Encrypt推奨）

### Step 1: サーバーの準備

```bash
# パッケージ更新
sudo apt update && sudo apt upgrade -y

# Dockerのインストール（まだの場合）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Composeのインストール
sudo apt install docker-compose-plugin -y

# ファイアウォール設定
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 2: リポジトリのクローン

```bash
# アプリケーション用ディレクトリ作成
sudo mkdir -p /opt/ict-construction
cd /opt/ict-construction

# リポジトリクローン
git clone https://github.com/takumanozawa/Hello-World.git .
```

### Step 3: 本番用環境変数の設定

```bash
# 環境変数ファイルを作成
cp backend/.env.example backend/.env

# 本番用に編集
sudo nano backend/.env
```

**本番環境の設定例:**
```env
# データベース
DATABASE_URL=postgresql+asyncpg://ict_user:強力なパスワード@postgres:5432/ict_construction

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=本番用アクセスキー
MINIO_SECRET_KEY=本番用シークレットキー

# セキュリティ（必ず変更！）
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS（実際のドメインに変更）
CORS_ORIGINS=https://ict-construction.example.com

# アプリケーション設定
APP_NAME=ICT施工Stage2管理システム
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# Email（実際のSMTP設定）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@example.com

# LINE通知（オプション）
LINE_CHANNEL_ACCESS_TOKEN=your-line-token
LINE_CHANNEL_SECRET=your-line-secret

# 外部API
WEATHER_API_KEY=your-openweathermap-api-key
```

### Step 4: 本番用Docker Compose設定

本番用のDocker Compose設定を作成:

```bash
sudo nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb-ha:pg15-latest
    container_name: ict_postgres_prod
    restart: always
    environment:
      POSTGRES_USER: ict_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ict_construction
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init_db.sql:/docker-entrypoint-initdb.d/01_init.sql
    command: postgres -c shared_preload_libraries=timescaledb
    networks:
      - ict_network

  redis:
    image: redis:7-alpine
    container_name: ict_redis_prod
    restart: always
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    networks:
      - ict_network

  minio:
    image: minio/minio:latest
    container_name: ict_minio_prod
    restart: always
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - ict_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ict_backend_prod
    restart: always
    env_file:
      - backend/.env
    depends_on:
      - postgres
      - redis
    networks:
      - ict_network
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ict_celery_worker_prod
    restart: always
    env_file:
      - backend/.env
    depends_on:
      - postgres
      - redis
    networks:
      - ict_network
    command: celery -A app.tasks.celery worker --loglevel=info

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ict_celery_beat_prod
    restart: always
    env_file:
      - backend/.env
    depends_on:
      - postgres
      - redis
    networks:
      - ict_network
    command: celery -A app.tasks.celery beat --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        VITE_API_URL: https://ict-construction.example.com/api
    container_name: ict_frontend_prod
    restart: always
    networks:
      - ict_network

  nginx:
    image: nginx:alpine
    container_name: ict_nginx_prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
      - frontend
    networks:
      - ict_network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  ict_network:
    driver: bridge
```

### Step 5: 本番用Dockerfileの作成

**バックエンド用:**
```bash
sudo nano backend/Dockerfile.prod
```

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    gdal-bin \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetryのインストール
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 依存関係ファイルのコピー
COPY pyproject.toml poetry.lock* ./

# 本番用依存関係のインストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --no-dev

# アプリケーションコードのコピー
COPY . .

# gunicornのインストール
RUN pip install gunicorn

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**フロントエンド用:**
```bash
sudo nano frontend/Dockerfile.prod
```

```dockerfile
FROM node:20-alpine as builder

WORKDIR /app

# pnpmのインストール
RUN npm install -g pnpm

# 依存関係ファイルのコピー
COPY package.json pnpm-lock.yaml* ./

# 依存関係のインストール
RUN pnpm install --frozen-lockfile

# アプリケーションコードのコピー
COPY . .

# ビルド引数
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# ビルド
RUN pnpm build

# 本番用イメージ
FROM nginx:alpine

# ビルド成果物をコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginxデフォルト設定を削除
RUN rm /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Step 6: Nginx設定

```bash
sudo mkdir -p nginx
sudo nano nginx/nginx.conf
```

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # ログ設定
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # gzip圧縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/json application/javascript;

    # アップストリーム定義
    upstream backend {
        server backend:8000;
    }

    # HTTPサーバー（HTTPSへリダイレクト）
    server {
        listen 80;
        server_name ict-construction.example.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPSサーバー
    server {
        listen 443 ssl http2;
        server_name ict-construction.example.com;

        # SSL証明書
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # SSL設定
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # フロントエンド
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # バックエンドAPI
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # 静的ファイルのキャッシュ
        location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
            root /usr/share/nginx/html;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### Step 7: SSL証明書の取得（Let's Encrypt）

```bash
# Certbotのインストール
sudo apt install certbot -y

# SSL証明書を取得
sudo certbot certonly --standalone -d ict-construction.example.com

# 証明書をNginx用ディレクトリにコピー
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/ict-construction.example.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/ict-construction.example.com/privkey.pem nginx/ssl/

# 証明書の自動更新設定
sudo crontab -e
# 以下を追加
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/ict-construction.example.com/*.pem /opt/ict-construction/nginx/ssl/ && docker-compose -f /opt/ict-construction/docker-compose.prod.yml restart nginx
```

### Step 8: デプロイ実行

```bash
# イメージをビルド
docker-compose -f docker-compose.prod.yml build

# サービスを起動
docker-compose -f docker-compose.prod.yml up -d

# ログを確認
docker-compose -f docker-compose.prod.yml logs -f

# マイグレーション実行
docker-compose -f docker-compose.prod.yml exec backend poetry run alembic upgrade head
```

### Step 9: 動作確認

```bash
# ヘルスチェック
curl https://ict-construction.example.com/api/health

# 期待される結果:
# {"status":"healthy","app_name":"ICT施工Stage2管理システム","version":"1.0.0"}
```

ブラウザで `https://ict-construction.example.com` にアクセスして確認。

### Step 10: 監視・ログ設定

```bash
# ログの確認
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs nginx

# リソース使用状況の確認
docker stats

# 自動再起動の確認
docker-compose -f docker-compose.prod.yml ps
```

---

## クラウド環境へのデプロイ

### AWS EC2へのデプロイ

1. **EC2インスタンスの起動**
   - AMI: Ubuntu 22.04 LTS
   - インスタンスタイプ: t3.medium以上推奨
   - ストレージ: 50GB以上
   - セキュリティグループ: 22, 80, 443ポート開放

2. **Elastic IPの割り当て**

3. **Route 53でDNS設定**

4. **上記の本番環境デプロイ手順を実行**

### Google Cloud Platform (GCP)へのデプロイ

1. **Compute Engineインスタンス作成**
   - マシンタイプ: e2-medium以上
   - ブートディスク: Ubuntu 22.04 LTS, 50GB

2. **静的IPアドレスの予約**

3. **Cloud DNSでDNS設定**

4. **上記の本番環境デプロイ手順を実行**

### Azure Virtual Machineへのデプロイ

1. **仮想マシンの作成**
   - サイズ: Standard_B2s以上
   - イメージ: Ubuntu 22.04 LTS

2. **パブリックIPアドレスの作成**

3. **Azure DNSでDNS設定**

4. **上記の本番環境デプロイ手順を実行**

---

## トラブルシューティング

### 1. Docker Composeが起動しない

```bash
# ログを確認
docker-compose logs

# ポート競合の確認
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000

# Dockerデーモンの再起動
sudo systemctl restart docker
```

### 2. データベース接続エラー

```bash
# PostgreSQLコンテナの確認
docker-compose ps postgres
docker-compose logs postgres

# データベースに直接接続
docker-compose exec postgres psql -U ict_user -d ict_construction

# 接続テスト
\conninfo
\dt
```

### 3. フロントエンドが表示されない

```bash
# Nginxログの確認
docker-compose logs nginx

# フロントエンドのビルド確認
docker-compose exec frontend ls -la /app/dist

# ブラウザのコンソールでエラー確認
```

### 4. SSL証明書のエラー

```bash
# 証明書の確認
sudo certbot certificates

# 証明書の更新
sudo certbot renew

# Nginxの設定テスト
docker-compose exec nginx nginx -t

# Nginxの再起動
docker-compose restart nginx
```

### 5. メモリ不足

```bash
# メモリ使用状況確認
free -h
docker stats

# Swapの追加（推奨）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 6. パフォーマンス問題

```bash
# データベースの最適化
docker-compose exec postgres psql -U ict_user -d ict_construction
VACUUM ANALYZE;

# Redisのメモリ確認
docker-compose exec redis redis-cli INFO memory

# ログファイルのローテーション
sudo logrotate -f /etc/logrotate.conf
```

---

## バックアップ・復元

### データベースのバックアップ

```bash
# バックアップ作成
docker-compose exec -T postgres pg_dump -U ict_user ict_construction > backup_$(date +%Y%m%d_%H%M%S).sql

# 圧縮
gzip backup_*.sql
```

### データベースの復元

```bash
# 復元
gunzip -c backup_20260118_120000.sql.gz | docker-compose exec -T postgres psql -U ict_user -d ict_construction
```

### 自動バックアップの設定

```bash
# バックアップスクリプト作成
sudo nano /opt/ict-construction/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/ict-construction/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# データベースバックアップ
docker-compose -f /opt/ict-construction/docker-compose.prod.yml exec -T postgres \
    pg_dump -U ict_user ict_construction | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 古いバックアップを削除（30日以上前）
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
# 実行権限付与
sudo chmod +x /opt/ict-construction/backup.sh

# cronで毎日実行
sudo crontab -e
# 以下を追加（毎日午前2時に実行）
0 2 * * * /opt/ict-construction/backup.sh
```

---

## アップデート手順

```bash
# 最新コードを取得
cd /opt/ict-construction
git pull origin main

# イメージを再ビルド
docker-compose -f docker-compose.prod.yml build

# サービスを再起動
docker-compose -f docker-compose.prod.yml up -d

# マイグレーション実行（必要な場合）
docker-compose -f docker-compose.prod.yml exec backend poetry run alembic upgrade head

# 古いイメージを削除
docker image prune -f
```

---

**デプロイ完了！**

システムは `https://ict-construction.example.com` で稼働しています。
