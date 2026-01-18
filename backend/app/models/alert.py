"""
アラート・通知関連モデル
"""
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.base import BaseModel


class AlertRule(Base, BaseModel):
    """アラートルール定義"""

    __tablename__ = "alert_rules"

    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False, index=True)
    # 'schedule_delay', 'speed_violation', 'vehicle_dwell',
    # 'low_productivity', 'weather_warning', 'water_level'

    description = Column(Text)

    # 条件（JSON形式）
    condition_config = Column(JSONB, nullable=False)
    # 例: {"threshold": 60, "unit": "km/h"}

    # アラートレベル
    severity = Column(String(20), nullable=False, default="warning")
    # 'info', 'warning', 'error', 'critical'

    # 適用範囲
    scope = Column(String(20), default="all")
    # 'all', 'site', 'vehicle', 'task'
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"))
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"))
    task_id = Column(UUID(as_uuid=True), ForeignKey("site_tasks.id"))

    # 通知設定
    notification_enabled = Column(String(10), default="True")
    notification_channels = Column(JSONB)
    # ["email", "line", "dashboard"]

    is_active = Column(String(10), default="True", index=True)

    def __repr__(self) -> str:
        return f"<AlertRule {self.rule_code}: {self.rule_name}>"


class Alert(Base, BaseModel):
    """アラート発生履歴"""

    __tablename__ = "alerts"

    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"))

    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # 関連エンティティ
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), index=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("site_tasks.id"))
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"))

    # 発生情報
    occurred_at = Column(Date, nullable=False, index=True)
    location = Column(Geography(geometry_type="POINT", srid=4326))

    # 詳細データ
    context_data = Column(JSONB)

    # 対応状況
    status = Column(String(20), default="new", index=True)
    # 'new', 'acknowledged', 'in_progress', 'resolved', 'dismissed'

    acknowledged_at = Column(Date)
    acknowledged_by = Column(UUID(as_uuid=True))
    resolved_at = Column(Date)
    resolved_by = Column(UUID(as_uuid=True))
    resolution_notes = Column(Text)

    # リレーション
    rule: Mapped[Optional["AlertRule"]] = relationship("AlertRule")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="alert",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type}: {self.title}>"


class Notification(Base, BaseModel):
    """通知履歴"""

    __tablename__ = "notifications"

    alert_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        index=True,
    )

    channel = Column(String(20), nullable=False)
    # 'email', 'line', 'push', 'sms'

    recipient_type = Column(String(20), nullable=False)
    # 'user', 'role', 'group'
    recipient_id = Column(UUID(as_uuid=True))
    recipient_address = Column(String(200))  # email, phone, LINE user ID

    subject = Column(String(200))
    body = Column(Text, nullable=False)

    # 送信状況
    status = Column(String(20), default="pending", index=True)
    # 'pending', 'sent', 'failed', 'read'

    sent_at = Column(Date, index=True)
    read_at = Column(Date)

    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # リレーション
    alert: Mapped[Optional["Alert"]] = relationship("Alert", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.channel} to {self.recipient_address}>"
