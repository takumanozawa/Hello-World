"""
モデルベースクラス
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class UUIDMixin:
    """UUIDプライマリキーミックスイン"""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


@declarative_mixin
class TimestampMixin:
    """作成日時・更新日時ミックスイン"""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


@declarative_mixin
class UserTrackingMixin:
    """ユーザー追跡ミックスイン"""

    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)


class BaseModel(UUIDMixin, TimestampMixin):
    """
    基本モデルクラス

    すべてのモデルの基底クラス
    UUID主キーと作成日時・更新日時を持つ
    """

    def to_dict(self) -> dict[str, Any]:
        """モデルを辞書に変換"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns  # type: ignore
        }
