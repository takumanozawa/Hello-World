-- データベース初期化スクリプト

-- PostGIS拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- TimescaleDB拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- UUID拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 日本語ロケール設定の確認
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_collation WHERE collname = 'ja_JP') THEN
        RAISE NOTICE '日本語ロケールが見つかりません。システムロケールを確認してください。';
    END IF;
END $$;

-- 基本的なインデックスの作成（マイグレーションで詳細設定）
COMMENT ON DATABASE ict_construction IS 'ICT施工Stage2管理システム データベース';

-- 初期ユーザーの作成は別途マイグレーションで実行
