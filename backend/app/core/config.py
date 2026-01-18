"""
アプリケーション設定
"""
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # アプリケーション
    APP_NAME: str = "ICT施工Stage2管理システム"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # データベース
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "ict-construction"
    MINIO_SECURE: bool = False

    # セキュリティ
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """CORS オリジンをリストに変換"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Email (オプション)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@ict-construction.com"

    # LINE Messaging API (オプション)
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    LINE_CHANNEL_SECRET: str = ""

    # 外部API
    WEATHER_API_KEY: str = ""

    # GPS設定
    GPS_UPDATE_INTERVAL_SECONDS: int = 10
    GPS_ACCURACY_THRESHOLD_METERS: float = 50.0

    # サイクルタイム設定
    CYCLE_LOADING_DWELL_SECONDS: int = 180  # 3分
    CYCLE_UNLOADING_DWELL_SECONDS: int = 120  # 2分
    CYCLE_MAX_WAITING_SECONDS: int = 1800  # 30分

    # アラート設定
    ALERT_SPEED_LIMIT_KMH: float = 60.0
    ALERT_DWELL_THRESHOLD_MINUTES: int = 30
    ALERT_SCHEDULE_DELAY_DAYS: int = 3


settings = Settings()  # type: ignore
