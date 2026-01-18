"""
現場関連モデル
"""
from datetime import date
from decimal import Decimal
from typing import List

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.base import BaseModel, UserTrackingMixin


class Site(Base, BaseModel, UserTrackingMixin):
    """現場マスタ"""

    __tablename__ = "sites"

    site_code = Column(String(50), unique=True, nullable=False, index=True)
    site_name = Column(String(200), nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326))
    address = Column(String(500))
    client_name = Column(String(200))
    contractor_name = Column(String(200))

    # 工期
    planned_start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=False)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)

    # 施工数量
    planned_volume = Column(Numeric(12, 2))  # 計画土量 (m³)
    actual_volume = Column(Numeric(12, 2), default=0)  # 実績土量 (m³)

    # ステータス
    status = Column(
        String(20),
        nullable=False,
        default="planning",
        index=True,
    )
    # 'planning', 'active', 'suspended', 'completed'

    # ジオフェンス（作業エリア）
    work_area_polygon = Column(Geography(geometry_type="POLYGON", srid=4326))

    # リレーション
    tasks: Mapped[List["SiteTask"]] = relationship(
        "SiteTask",
        back_populates="site",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("planned_end_date >= planned_start_date", name="chk_dates"),
    )

    def __repr__(self) -> str:
        return f"<Site {self.site_code}: {self.site_name}>"


class SiteTask(Base, BaseModel):
    """工程タスク"""

    __tablename__ = "site_tasks"

    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("site_tasks.id"),
        index=True,
    )

    task_code = Column(String(50), nullable=False)
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False)
    # 'excavation', 'transport', 'backfill', 'inspection'

    # 計画
    planned_start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=False)
    planned_volume = Column(Numeric(12, 2))
    planned_manhours = Column(Numeric(8, 2))

    # 実績
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    actual_volume = Column(Numeric(12, 2), default=0)
    actual_manhours = Column(Numeric(8, 2), default=0)

    # 進捗
    progress_rate = Column(Numeric(5, 2), default=0)  # %
    status = Column(String(20), default="pending", index=True)
    # 'pending', 'in_progress', 'completed', 'delayed'

    # 依存関係
    dependencies = Column(JSONB)  # [{"task_id": "xxx", "type": "FS"}]

    # 順序
    display_order = Column(Integer)

    # リレーション
    site: Mapped["Site"] = relationship("Site", back_populates="tasks")
    parent_task: Mapped["SiteTask"] = relationship(
        "SiteTask",
        remote_side="SiteTask.id",
        backref="child_tasks",
    )

    __table_args__ = (
        CheckConstraint(
            "planned_end_date >= planned_start_date",
            name="chk_task_dates",
        ),
        CheckConstraint(
            "progress_rate BETWEEN 0 AND 100",
            name="chk_progress",
        ),
    )

    def __repr__(self) -> str:
        return f"<SiteTask {self.task_code}: {self.task_name}>"


class TaskProgress(Base, BaseModel):
    """日別進捗"""

    __tablename__ = "task_progress"

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("site_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    progress_date = Column(Date, nullable=False, index=True)

    volume_completed = Column(Numeric(12, 2), nullable=False)  # 当日施工量
    cumulative_volume = Column(Numeric(12, 2), nullable=False)  # 累計施工量
    manhours = Column(Numeric(8, 2))

    weather = Column(String(50))
    temperature_max = Column(Numeric(4, 1))
    temperature_min = Column(Numeric(4, 1))
    rainfall = Column(Numeric(6, 2))  # mm

    remarks = Column(Text)
    created_by = Column(UUID(as_uuid=True))

    # リレーション
    task: Mapped["SiteTask"] = relationship("SiteTask")

    __table_args__ = (
        CheckConstraint("volume_completed >= 0", name="chk_volume_positive"),
        {"unique": ("task_id", "progress_date")},
    )

    def __repr__(self) -> str:
        return f"<TaskProgress {self.progress_date}: {self.volume_completed}m³>"


class SiteDailyReport(Base, BaseModel):
    """日報"""

    __tablename__ = "site_daily_reports"

    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_date = Column(Date, nullable=False, index=True)

    weather_am = Column(String(50))
    weather_pm = Column(String(50))
    temperature_max = Column(Numeric(4, 1))
    temperature_min = Column(Numeric(4, 1))

    # 施工数量
    daily_volume = Column(Numeric(12, 2))
    cumulative_volume = Column(Numeric(12, 2))

    # 人員・機械
    worker_count = Column(Integer)
    vehicle_count = Column(Integer)

    # 作業内容
    work_description = Column(Text)
    issues = Column(Text)
    tomorrow_plan = Column(Text)

    # 安全
    safety_meeting = Column(String(10), default="False")
    accidents = Column(Text)
    near_misses = Column(Text)

    # 承認フロー
    status = Column(String(20), default="draft")
    # 'draft', 'submitted', 'approved'
    submitted_at = Column(Date)
    submitted_by = Column(UUID(as_uuid=True))
    approved_at = Column(Date)
    approved_by = Column(UUID(as_uuid=True))

    # リレーション
    site: Mapped["Site"] = relationship("Site")

    __table_args__ = ({"unique": ("site_id", "report_date")},)

    def __repr__(self) -> str:
        return f"<SiteDailyReport {self.report_date}: {self.daily_volume}m³>"
