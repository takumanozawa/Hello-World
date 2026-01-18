"""
シミュレーション関連モデル
"""
from sqlalchemy import Column, Date, ForeignKey, Interval, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.base import BaseModel


class Simulation(Base, BaseModel):
    """シミュレーション設定"""

    __tablename__ = "simulations"

    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sites.id"),
        nullable=False,
        index=True,
    )
    task_id = Column(UUID(as_uuid=True), ForeignKey("site_tasks.id"))

    simulation_name = Column(String(200), nullable=False)
    simulation_type = Column(String(50), nullable=False, index=True)
    # 'cycle_time', 'resource_allocation', 'schedule_optimization'

    # 入力パラメータ
    parameters = Column(JSONB, nullable=False)
    """
    例:
    {
        "excavation_volume": 5000,
        "truck_capacity": 10,
        "loading_time": 5,
        "transport_distance": 3.5,
        "unloading_time": 3,
        "trucks_count": 5
    }
    """

    # 実行情報
    status = Column(String(20), default="pending", index=True)
    # 'pending', 'running', 'completed', 'failed'

    started_at = Column(Date)
    completed_at = Column(Date)
    duration = Column(Interval)

    error_message = Column(Text)

    created_by = Column(UUID(as_uuid=True))

    # リレーション
    results: Mapped[list["SimulationResult"]] = relationship(
        "SimulationResult",
        back_populates="simulation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Simulation {self.simulation_name}: {self.simulation_type}>"


class SimulationResult(Base, BaseModel):
    """シミュレーション結果"""

    __tablename__ = "simulation_results"

    simulation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 結果データ
    results = Column(JSONB, nullable=False)
    """
    例:
    {
        "total_cycles": 50,
        "average_cycle_time": 45,
        "total_volume": 500,
        "efficiency_rate": 85.5,
        "bottleneck": "loading",
        "recommendations": ["重機を1台追加", "待機エリア拡大"]
    }
    """

    # 時系列データ
    timeline_data = Column(JSONB)

    # 比較用実績データ
    actual_data = Column(JSONB)
    variance = Column(JSONB)  # 予実差異

    # リレーション
    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results")

    def __repr__(self) -> str:
        return f"<SimulationResult for {self.simulation_id}>"
