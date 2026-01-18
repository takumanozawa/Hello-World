"""
車両・リソース関連モデル
"""
from datetime import date, time
from decimal import Decimal
from typing import List

from geoalchemy2 import Geography
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.base import BaseModel


class Vehicle(Base, BaseModel):
    """車両マスタ"""

    __tablename__ = "vehicles"

    vehicle_code = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_name = Column(String(100), nullable=False)
    vehicle_type = Column(String(50), nullable=False, index=True)
    # 'dump_truck', 'backhoe', 'bulldozer', 'excavator'

    # 仕様
    capacity = Column(Numeric(8, 2))  # 積載量 (m³ or ton)
    manufacturer = Column(String(100))
    model_name = Column(String(100))
    year_manufactured = Column(Integer)

    # GPS端末
    gps_device_id = Column(String(100), index=True)
    gps_device_type = Column(String(50))
    # 'gpsnext', 'trackimo', 'smartphone'

    # ステータス
    status = Column(String(20), default="active", index=True)
    # 'active', 'maintenance', 'retired'

    # 現在の配置
    current_site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), index=True)

    # 車検・点検
    inspection_date = Column(Date)
    next_inspection = Column(Date)

    # 燃費・稼働
    fuel_efficiency = Column(Numeric(6, 2))  # L/hour
    hourly_cost = Column(Numeric(10, 2))  # 円/時間

    # リレーション
    gps_positions: Mapped[List["GPSPosition"]] = relationship(
        "GPSPosition",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    cycles: Mapped[List["VehicleCycle"]] = relationship(
        "VehicleCycle",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Vehicle {self.vehicle_code}: {self.vehicle_name}>"


class Worker(Base, BaseModel):
    """作業員マスタ"""

    __tablename__ = "workers"

    worker_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    name_kana = Column(String(100))

    role = Column(String(50), nullable=False, index=True)
    # 'operator', 'driver', 'laborer', 'foreman', 'supervisor'

    qualifications = Column(JSONB)  # ["重機1級", "玉掛け"]

    phone_number = Column(String(20))
    email = Column(String(100))

    employment_type = Column(String(20))
    # 'full_time', 'part_time', 'contractor'

    daily_rate = Column(Numeric(10, 2))

    status = Column(String(20), default="active", index=True)

    current_site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), index=True)

    def __repr__(self) -> str:
        return f"<Worker {self.worker_code}: {self.name}>"


class ResourceAssignment(Base, BaseModel):
    """リソース配置"""

    __tablename__ = "resource_assignments"

    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("site_tasks.id", ondelete="SET NULL"),
        index=True,
    )

    resource_type = Column(String(20), nullable=False)
    # 'vehicle', 'worker'

    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), index=True)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), index=True)

    assignment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time)
    end_time = Column(Time)

    actual_start_time = Column(Date)
    actual_end_time = Column(Date)

    status = Column(String(20), default="assigned")
    # 'assigned', 'in_progress', 'completed', 'cancelled'

    notes = Column(Text)

    # リレーション
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")
    worker: Mapped["Worker"] = relationship("Worker")

    __table_args__ = (
        CheckConstraint(
            "(resource_type = 'vehicle' AND vehicle_id IS NOT NULL) OR "
            "(resource_type = 'worker' AND worker_id IS NOT NULL)",
            name="chk_resource_exists",
        ),
    )

    def __repr__(self) -> str:
        return f"<ResourceAssignment {self.resource_type} on {self.assignment_date}>"


class GPSPosition(Base):
    """GPS位置データ (TimescaleDB Hypertable)"""

    __tablename__ = "gps_positions"

    time = Column(Date, primary_key=True, nullable=False)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    altitude = Column(Numeric(8, 2))

    speed = Column(Numeric(6, 2))  # km/h
    heading = Column(Numeric(5, 2))  # 方位角 0-360
    accuracy = Column(Numeric(6, 2))  # GPS精度 (m)

    # デバイス情報
    device_id = Column(String(100))
    battery_level = Column(Integer)  # %

    # 状態推定
    estimated_state = Column(String(20))
    # 'loading', 'loaded_moving', 'unloading', 'empty_moving', 'idle'

    # 生データ
    raw_data = Column(JSONB)

    # リレーション
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="gps_positions")

    def __repr__(self) -> str:
        return f"<GPSPosition {self.vehicle_id} at {self.time}>"


class VehicleCycle(Base, BaseModel):
    """運搬サイクル"""

    __tablename__ = "vehicle_cycles"

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id"),
        nullable=False,
        index=True,
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id"),
        nullable=False,
        index=True,
    )
    cycle_date = Column(Date, nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)  # 当日の何回目

    # 開始・終了
    start_time = Column(Date, nullable=False)
    end_time = Column(Date)
    total_duration = Column(Interval)  # 総所要時間

    # 積込み
    loading_location = Column(Geography(geometry_type="POINT", srid=4326))
    loading_start = Column(Date)
    loading_end = Column(Date)
    loading_duration = Column(Interval)

    # 運搬（積載）
    loaded_moving_start = Column(Date)
    loaded_moving_end = Column(Date)
    loaded_duration = Column(Interval)
    loaded_distance = Column(Numeric(8, 2))  # km

    # 荷降ろし
    unloading_location = Column(Geography(geometry_type="POINT", srid=4326))
    unloading_start = Column(Date)
    unloading_end = Column(Date)
    unloading_duration = Column(Interval)

    # 運搬（空車）
    empty_moving_start = Column(Date)
    empty_moving_end = Column(Date)
    empty_duration = Column(Interval)
    empty_distance = Column(Numeric(8, 2))  # km

    # 待機
    waiting_duration = Column(Interval)

    # 運搬量
    volume = Column(Numeric(8, 2))  # m³

    # 状態
    status = Column(String(20), default="in_progress", index=True)
    # 'in_progress', 'completed', 'aborted'

    # 異常検知
    has_anomaly = Column(String(10), default="False")
    anomaly_type = Column(String(50))
    # 'long_waiting', 'speed_violation', 'route_deviation'

    # リレーション
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="cycles")

    __table_args__ = ({"unique": ("vehicle_id", "cycle_date", "cycle_number")},)

    def __repr__(self) -> str:
        return f"<VehicleCycle {self.vehicle_id} #{self.cycle_number} on {self.cycle_date}>"


class Geofence(Base, BaseModel):
    """ジオフェンス定義"""

    __tablename__ = "geofences"

    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    fence_type = Column(String(50), nullable=False)
    # 'loading_zone', 'unloading_zone', 'waiting_area', 'restricted_area'

    geometry = Column(Geography(geometry_type="POLYGON", srid=4326), nullable=False)

    # アラート設定
    alert_on_entry = Column(String(10), default="False")
    alert_on_exit = Column(String(10), default="False")
    alert_on_dwell = Column(String(10), default="False")
    dwell_threshold = Column(Interval)  # 滞留判定時間

    is_active = Column(String(10), default="True")

    def __repr__(self) -> str:
        return f"<Geofence {self.name}: {self.fence_type}>"
