#!/bin/bash

###############################################################################
# ICT施工Stage2管理システム - デプロイスクリプト
# 使い方: ./scripts/deploy.sh [local|production]
###############################################################################

set -e

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 引数チェック
if [ $# -eq 0 ]; then
    log_error "引数が必要です。使い方: ./scripts/deploy.sh [local|production]"
    exit 1
fi

ENVIRONMENT=$1
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)

log_info "🚀 ICT施工Stage2管理システムをデプロイします"
log_info "環境: $ENVIRONMENT"
log_info "プロジェクトルート: $PROJECT_ROOT"

###############################################################################
# ローカル環境デプロイ
###############################################################################

deploy_local() {
    log_info "📦 ローカル環境にデプロイします..."

    # 環境変数の確認
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        log_warning ".envファイルが見つかりません。サンプルからコピーします。"
        cp "$PROJECT_ROOT/backend/.env.example" "$PROJECT_ROOT/backend/.env"
        log_warning "backend/.envを編集してください。"
        read -p "編集を完了しましたか? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "デプロイを中止しました。"
            exit 1
        fi
    fi

    # Dockerの確認
    if ! command -v docker &> /dev/null; then
        log_error "Dockerがインストールされていません。"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Composeがインストールされていません。"
        exit 1
    fi

    # Docker Composeコマンドの決定
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi

    log_info "Docker Composeコマンド: $DOCKER_COMPOSE"

    # 古いコンテナを停止
    log_info "既存のコンテナを停止します..."
    $DOCKER_COMPOSE down || true

    # イメージをビルド
    log_info "Dockerイメージをビルドします..."
    $DOCKER_COMPOSE build

    # コンテナを起動
    log_info "コンテナを起動します..."
    $DOCKER_COMPOSE up -d

    # ヘルスチェック
    log_info "サービスの起動を待機中..."
    sleep 10

    # PostgreSQLの起動確認
    log_info "PostgreSQLの起動を確認中..."
    for i in {1..30}; do
        if $DOCKER_COMPOSE exec -T postgres pg_isready -U ict_user &> /dev/null; then
            log_success "PostgreSQLが起動しました"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQLの起動がタイムアウトしました"
            exit 1
        fi
        echo -n "."
        sleep 2
    done

    # データベースマイグレーション
    log_info "データベースマイグレーションを実行します..."
    $DOCKER_COMPOSE exec -T backend poetry run alembic upgrade head

    # サービスの状態確認
    log_info "サービスの状態:"
    $DOCKER_COMPOSE ps

    # アクセスURL表示
    echo ""
    log_success "✅ デプロイが完了しました！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📱 アクセスURL:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🌐 フロントエンド: http://localhost:3000"
    echo "  🔧 バックエンドAPI: http://localhost:8000"
    echo "  📚 API Docs: http://localhost:8000/docs"
    echo "  📦 MinIO Console: http://localhost:9001"
    echo "      (ID: minioadmin / PW: minioadmin123)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📝 ログの確認: $DOCKER_COMPOSE logs -f"
    echo "⏹️  停止: $DOCKER_COMPOSE stop"
    echo "🗑️  削除: $DOCKER_COMPOSE down -v"
    echo ""
}

###############################################################################
# 本番環境デプロイ
###############################################################################

deploy_production() {
    log_info "🏭 本番環境にデプロイします..."

    # root権限チェック
    if [ "$EUID" -ne 0 ]; then
        log_error "本番環境へのデプロイにはroot権限が必要です。"
        log_info "sudo ./scripts/deploy.sh production を実行してください。"
        exit 1
    fi

    # 環境変数の確認
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        log_error "backend/.envファイルが見つかりません。"
        log_info "backend/.env.exampleを参考に作成してください。"
        exit 1
    fi

    # Docker Compose設定の確認
    if [ ! -f "$PROJECT_ROOT/docker-compose.prod.yml" ]; then
        log_error "docker-compose.prod.ymlが見つかりません。"
        exit 1
    fi

    # Nginx設定の確認
    if [ ! -f "$PROJECT_ROOT/nginx/nginx.conf" ]; then
        log_error "nginx/nginx.confが見つかりません。"
        exit 1
    fi

    # SSL証明書の確認
    if [ ! -f "$PROJECT_ROOT/nginx/ssl/fullchain.pem" ] || [ ! -f "$PROJECT_ROOT/nginx/ssl/privkey.pem" ]; then
        log_warning "SSL証明書が見つかりません。"
        log_info "Let's Encryptで証明書を取得してください。"
        log_info "例: certbot certonly --standalone -d your-domain.com"
        read -p "証明書なしで続行しますか? (開発環境のみ) (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # 確認プロンプト
    log_warning "本番環境にデプロイします。この操作は既存のサービスに影響を与える可能性があります。"
    read -p "続行しますか? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "デプロイを中止しました。"
        exit 1
    fi

    # バックアップ
    log_info "データベースをバックアップします..."
    BACKUP_DIR="$PROJECT_ROOT/backups"
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

    if docker ps | grep -q ict_postgres_prod; then
        docker exec ict_postgres_prod pg_dump -U ict_user ict_construction > "$BACKUP_FILE" 2>/dev/null || log_warning "バックアップに失敗しました（初回デプロイの場合は正常です）"
        if [ -f "$BACKUP_FILE" ]; then
            gzip "$BACKUP_FILE"
            log_success "バックアップ完了: ${BACKUP_FILE}.gz"
        fi
    else
        log_warning "既存のデータベースコンテナが見つかりません（初回デプロイの場合は正常です）"
    fi

    # Docker Composeコマンドの決定
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi

    # イメージをビルド
    log_info "Dockerイメージをビルドします..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml build

    # コンテナを起動
    log_info "コンテナを起動します..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d

    # ヘルスチェック
    log_info "サービスの起動を待機中..."
    sleep 15

    # PostgreSQLの起動確認
    log_info "PostgreSQLの起動を確認中..."
    for i in {1..30}; do
        if docker exec ict_postgres_prod pg_isready -U ict_user &> /dev/null; then
            log_success "PostgreSQLが起動しました"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQLの起動がタイムアウトしました"
            exit 1
        fi
        echo -n "."
        sleep 2
    done

    # データベースマイグレーション
    log_info "データベースマイグレーションを実行します..."
    docker exec ict_backend_prod poetry run alembic upgrade head

    # サービスの状態確認
    log_info "サービスの状態:"
    $DOCKER_COMPOSE -f docker-compose.prod.yml ps

    # ヘルスチェック
    log_info "APIヘルスチェックを実行します..."
    sleep 5
    if curl -f http://localhost/api/health &> /dev/null; then
        log_success "APIが正常に動作しています"
    else
        log_warning "APIヘルスチェックに失敗しました。ログを確認してください。"
    fi

    # 古いイメージを削除
    log_info "未使用のDockerイメージを削除します..."
    docker image prune -f

    # 完了メッセージ
    echo ""
    log_success "✅ 本番環境へのデプロイが完了しました！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 次のステップ:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  1. ブラウザでアクセスして動作確認"
    echo "  2. ログを監視: $DOCKER_COMPOSE -f docker-compose.prod.yml logs -f"
    echo "  3. 監視システムの設定（Prometheus + Grafana推奨）"
    echo "  4. バックアップの自動化設定"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

###############################################################################
# メイン処理
###############################################################################

case $ENVIRONMENT in
    local)
        deploy_local
        ;;
    production|prod)
        deploy_production
        ;;
    *)
        log_error "不明な環境: $ENVIRONMENT"
        log_info "使い方: ./scripts/deploy.sh [local|production]"
        exit 1
        ;;
esac
