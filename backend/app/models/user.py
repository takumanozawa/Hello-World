"""
ユーザー・権限管理モデル
"""
from sqlalchemy import ARRAY, Column, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.base import BaseModel


class User(Base, BaseModel):
    """ユーザー"""

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))

    role = Column(String(20), nullable=False, default="viewer", index=True)
    # 'admin', 'manager', 'supervisor', 'operator', 'viewer'

    # 所属
    company_name = Column(String(100))
    department = Column(String(100))

    # 権限
    permissions = Column(JSONB)
    # ["sites:read", "sites:write", "vehicles:read"]

    # アクセス可能な現場
    accessible_sites = Column(ARRAY(UUID(as_uuid=True)))

    # アカウント状態
    is_active = Column(String(10), default="True", index=True)
    is_email_verified = Column(String(10), default="False")

    # 最終ログイン
    last_login_at = Column(Date)
    last_login_ip = Column(INET)

    # パスワードリセット
    reset_token = Column(String(255))
    reset_token_expires = Column(Date)

    # リレーション
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}: {self.full_name}>"


class RefreshToken(Base, BaseModel):
    """リフレッシュトークン"""

    __tablename__ = "refresh_tokens"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(255), unique=True, nullable=False, index=True)

    expires_at = Column(Date, nullable=False, index=True)
    is_revoked = Column(String(10), default="False")

    device_info = Column(JSONB)
    ip_address = Column(INET)

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken for user {self.user_id}>"


class AuditLog(Base):
    """操作ログ"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    action = Column(String(50), nullable=False)
    # 'create', 'update', 'delete', 'login', 'logout'

    entity_type = Column(String(50), index=True)
    entity_id = Column(UUID(as_uuid=True), index=True)

    changes = Column(JSONB)  # 変更内容

    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(Date, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"
