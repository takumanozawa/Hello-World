"""
現場関連スキーマ
"""
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# 現場（Site）スキーマ
class SiteBase(BaseModel):
    """現場基本スキーマ"""

    site_code: str = Field(..., max_length=50, description="現場コード")
    site_name: str = Field(..., max_length=200, description="現場名")
    address: Optional[str] = Field(None, max_length=500, description="住所")
    client_name: Optional[str] = Field(None, max_length=200, description="発注者名")
    contractor_name: Optional[str] = Field(None, max_length=200, description="施工会社名")

    planned_start_date: date = Field(..., description="計画開始日")
    planned_end_date: date = Field(..., description="計画終了日")
    planned_volume: Optional[Decimal] = Field(None, description="計画土量 (m³)")

    status: str = Field(default="planning", description="ステータス")


class SiteCreate(SiteBase):
    """現場作成スキーマ"""

    location: Optional[dict[str, float]] = Field(
        None, description="位置情報 {lat: float, lng: float}"
    )


class SiteUpdate(BaseModel):
    """現場更新スキーマ"""

    site_name: Optional[str] = None
    address: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    planned_volume: Optional[Decimal] = None
    actual_volume: Optional[Decimal] = None
    status: Optional[str] = None


class SiteResponse(SiteBase):
    """現場レスポンススキーマ"""

    id: UUID
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_volume: Decimal = Decimal("0")

    # 計算フィールド
    progress_rate: Optional[Decimal] = Field(None, description="進捗率 (%)")

    class Config:
        from_attributes = True


# タスク（SiteTask）スキーマ
class TaskBase(BaseModel):
    """タスク基本スキーマ"""

    task_code: str = Field(..., max_length=50)
    task_name: str = Field(..., max_length=200)
    task_type: str = Field(..., max_length=50)

    planned_start_date: date
    planned_end_date: date
    planned_volume: Optional[Decimal] = None
    planned_manhours: Optional[Decimal] = None


class TaskCreate(TaskBase):
    """タスク作成スキーマ"""

    site_id: UUID
    parent_task_id: Optional[UUID] = None
    dependencies: Optional[list[dict[str, Any]]] = None


class TaskUpdate(BaseModel):
    """タスク更新スキーマ"""

    task_name: Optional[str] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    progress_rate: Optional[Decimal] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    """タスクレスポンススキーマ"""

    id: UUID
    site_id: UUID
    parent_task_id: Optional[UUID] = None

    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    actual_volume: Decimal = Decimal("0")
    actual_manhours: Decimal = Decimal("0")

    progress_rate: Decimal = Decimal("0")
    status: str

    class Config:
        from_attributes = True


# 進捗（TaskProgress）スキーマ
class TaskProgressBase(BaseModel):
    """進捗基本スキーマ"""

    progress_date: date
    volume_completed: Decimal = Field(..., description="当日施工量 (m³)")
    cumulative_volume: Decimal = Field(..., description="累計施工量 (m³)")
    manhours: Optional[Decimal] = None

    weather: Optional[str] = None
    temperature_max: Optional[Decimal] = None
    temperature_min: Optional[Decimal] = None
    rainfall: Optional[Decimal] = None

    remarks: Optional[str] = None


class TaskProgressCreate(TaskProgressBase):
    """進捗作成スキーマ"""

    task_id: UUID


class TaskProgressResponse(TaskProgressBase):
    """進捗レスポンススキーマ"""

    id: UUID
    task_id: UUID

    class Config:
        from_attributes = True


# 日報（SiteDailyReport）スキーマ
class DailyReportBase(BaseModel):
    """日報基本スキーマ"""

    report_date: date

    weather_am: Optional[str] = None
    weather_pm: Optional[str] = None
    temperature_max: Optional[Decimal] = None
    temperature_min: Optional[Decimal] = None

    daily_volume: Optional[Decimal] = None
    cumulative_volume: Optional[Decimal] = None

    worker_count: Optional[int] = None
    vehicle_count: Optional[int] = None

    work_description: Optional[str] = None
    issues: Optional[str] = None
    tomorrow_plan: Optional[str] = None

    safety_meeting: bool = False
    accidents: Optional[str] = None
    near_misses: Optional[str] = None


class DailyReportCreate(DailyReportBase):
    """日報作成スキーマ"""

    site_id: UUID


class DailyReportUpdate(BaseModel):
    """日報更新スキーマ"""

    daily_volume: Optional[Decimal] = None
    work_description: Optional[str] = None
    issues: Optional[str] = None
    status: Optional[str] = None


class DailyReportResponse(DailyReportBase):
    """日報レスポンススキーマ"""

    id: UUID
    site_id: UUID
    status: str

    class Config:
        from_attributes = True
