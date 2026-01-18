"""
Alembic マイグレーション環境設定
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base

# すべてのモデルをインポート
from app.models.alert import Alert, AlertRule, Notification  # noqa: F401
from app.models.simulation import Simulation, SimulationResult  # noqa: F401
from app.models.site import Site, SiteDailyReport, SiteTask, TaskProgress  # noqa: F401
from app.models.user import AuditLog, RefreshToken, User  # noqa: F401
from app.models.vehicle import (  # noqa: F401
    GPSPosition,
    Geofence,
    ResourceAssignment,
    Vehicle,
    VehicleCycle,
    Worker,
)

# Alembic Config オブジェクト
config = context.config

# ロギング設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータ
target_metadata = Base.metadata

# データベースURL設定
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))


def run_migrations_offline() -> None:
    """
    オフラインモードでマイグレーションを実行
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """マイグレーション実行"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期マイグレーション実行"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL.replace("+asyncpg", "")  # type: ignore

    connectable = async_engine_from_config(
        configuration,  # type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    オンラインモードでマイグレーションを実行
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
