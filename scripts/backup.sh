#!/bin/bash

###############################################################################
# ICT施工Stage2管理システム - バックアップスクリプト
# 使い方: ./scripts/backup.sh
###############################################################################

set -e

# カラー出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BACKUP_DIR="$PROJECT_ROOT/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo -e "${BLUE}[INFO]${NC} バックアップを開始します..."

# バックアップディレクトリ作成
mkdir -p "$BACKUP_DIR"

# PostgreSQLのバックアップ
echo -e "${BLUE}[INFO]${NC} PostgreSQLをバックアップします..."
if docker ps | grep -q ict_postgres; then
    CONTAINER_NAME="ict_postgres"
elif docker ps | grep -q ict_postgres_prod; then
    CONTAINER_NAME="ict_postgres_prod"
else
    echo -e "${BLUE}[INFO]${NC} PostgreSQLコンテナが見つかりません。スキップします。"
    exit 1
fi

docker exec $CONTAINER_NAME pg_dump -U ict_user ict_construction | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
echo -e "${GREEN}[SUCCESS]${NC} データベースバックアップ: $BACKUP_DIR/db_$DATE.sql.gz"

# MinIOのバックアップ（オプション）
echo -e "${BLUE}[INFO]${NC} MinIOデータをバックアップします..."
if docker ps | grep -q ict_minio; then
    MINIO_CONTAINER="ict_minio"
elif docker ps | grep -q ict_minio_prod; then
    MINIO_CONTAINER="ict_minio_prod"
else
    echo -e "${BLUE}[INFO]${NC} MinIOコンテナが見つかりません。スキップします。"
    MINIO_CONTAINER=""
fi

if [ -n "$MINIO_CONTAINER" ]; then
    docker exec $MINIO_CONTAINER tar czf - /data 2>/dev/null > "$BACKUP_DIR/minio_$DATE.tar.gz" || true
    echo -e "${GREEN}[SUCCESS]${NC} MinIOバックアップ: $BACKUP_DIR/minio_$DATE.tar.gz"
fi

# 古いバックアップを削除（30日以上前）
echo -e "${BLUE}[INFO]${NC} 古いバックアップを削除します（30日以上前）..."
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "minio_*.tar.gz" -mtime +30 -delete

# バックアップサイズ表示
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo -e "${GREEN}[SUCCESS]${NC} バックアップが完了しました"
echo -e "${BLUE}[INFO]${NC} バックアップディレクトリ: $BACKUP_DIR"
echo -e "${BLUE}[INFO]${NC} 合計サイズ: $TOTAL_SIZE"

# バックアップリスト表示
echo ""
echo "最近のバックアップ:"
ls -lht "$BACKUP_DIR" | head -10
