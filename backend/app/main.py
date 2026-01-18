"""
FastAPI メインアプリケーション
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    アプリケーションのライフサイクル管理
    """
    # 起動時の処理
    print("🚀 ICT施工Stage2管理システム起動中...")
    print(f"📍 環境: {'開発' if settings.DEBUG else '本番'}")

    yield

    # 終了時の処理
    print("👋 ICT施工Stage2管理システム終了")


# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="河道掘削工事向けの統合施工管理システム",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ヘルスチェック
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    ヘルスチェックエンドポイント
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    ルートエンドポイント
    """
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.DEBUG else "Disabled in production",
        }
    )


# APIルーター登録（後で追加）
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")
