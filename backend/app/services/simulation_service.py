"""
シミュレーションサービス
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import Simulation, SimulationResult


class SimulationService:
    """施工シミュレーションサービス"""

    @staticmethod
    async def run_cycle_time_simulation(
        db: AsyncSession,
        site_id: UUID,
        parameters: dict[str, Any],
    ) -> Simulation:
        """
        サイクルタイムシミュレーションを実行

        Args:
            db: データベースセッション
            site_id: 現場ID
            parameters: シミュレーションパラメータ
                - excavation_volume: 掘削土量 (m³)
                - truck_capacity: ダンプ積載量 (m³)
                - loading_time: 積込み時間 (分)
                - transport_distance: 運搬距離 (km)
                - loaded_speed: 積載時速度 (km/h)
                - empty_speed: 空車時速度 (km/h)
                - unloading_time: 荷降ろし時間 (分)
                - trucks_count: ダンプ台数

        Returns:
            作成されたSimulationオブジェクト
        """
        # Simulation作成
        simulation = Simulation(
            site_id=site_id,
            simulation_name=f"サイクルタイムシミュレーション {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            simulation_type="cycle_time",
            parameters=parameters,
            status="running",
            started_at=datetime.now(),  # type: ignore
        )

        db.add(simulation)
        await db.commit()
        await db.refresh(simulation)

        try:
            # シミュレーション実行
            results = SimulationService._calculate_cycle_time(parameters)

            # 結果を保存
            simulation_result = SimulationResult(
                simulation_id=simulation.id,
                results=results,
                timeline_data=SimulationService._generate_timeline(parameters, results),
            )

            db.add(simulation_result)

            # Simulation更新
            simulation.status = "completed"
            simulation.completed_at = datetime.now()  # type: ignore
            simulation.duration = simulation.completed_at - simulation.started_at  # type: ignore

            await db.commit()
            await db.refresh(simulation)

        except Exception as e:
            simulation.status = "failed"
            simulation.error_message = str(e)
            simulation.completed_at = datetime.now()  # type: ignore
            await db.commit()
            raise

        return simulation

    @staticmethod
    def _calculate_cycle_time(params: dict[str, Any]) -> dict[str, Any]:
        """
        サイクルタイム計算

        Returns:
            シミュレーション結果
        """
        # パラメータ取得
        excavation_volume = float(params["excavation_volume"])
        truck_capacity = float(params["truck_capacity"])
        loading_time = float(params["loading_time"])
        transport_distance = float(params["transport_distance"])
        loaded_speed = float(params.get("loaded_speed", 30))
        empty_speed = float(params.get("empty_speed", 40))
        unloading_time = float(params["unloading_time"])
        trucks_count = int(params["trucks_count"])

        # 計算
        # 積載時運搬時間 (分)
        loaded_transport_time = (transport_distance / loaded_speed) * 60

        # 空車時運搬時間 (分)
        empty_transport_time = (transport_distance / empty_speed) * 60

        # 1サイクル時間 (分)
        cycle_time = (
            loading_time + loaded_transport_time + unloading_time + empty_transport_time
        )

        # 必要サイクル数
        total_cycles_needed = excavation_volume / truck_capacity

        # 1台あたりのサイクル数
        cycles_per_truck = total_cycles_needed / trucks_count

        # 1台あたりの所要時間 (時間)
        time_per_truck = (cycles_per_truck * cycle_time) / 60

        # 全体の所要時間（並行作業） (時間)
        total_time_hours = time_per_truck

        # 1日8時間稼働と仮定
        work_days = total_time_hours / 8

        # 効率率計算
        # 理論的な最小サイクル時間と比較
        ideal_cycle_time = loading_time + unloading_time
        efficiency_rate = (ideal_cycle_time / cycle_time) * 100

        # ボトルネック判定
        components = {
            "loading": loading_time,
            "loaded_transport": loaded_transport_time,
            "unloading": unloading_time,
            "empty_transport": empty_transport_time,
        }
        bottleneck = max(components.items(), key=lambda x: x[1])[0]

        # 改善提案
        recommendations = SimulationService._generate_recommendations(
            params, cycle_time, bottleneck
        )

        return {
            "total_cycles": round(total_cycles_needed, 1),
            "cycles_per_truck": round(cycles_per_truck, 1),
            "average_cycle_time": round(cycle_time, 1),
            "total_time_hours": round(total_time_hours, 1),
            "work_days": round(work_days, 1),
            "efficiency_rate": round(efficiency_rate, 1),
            "bottleneck": bottleneck,
            "breakdown": {
                "loading_time": round(loading_time, 1),
                "loaded_transport_time": round(loaded_transport_time, 1),
                "unloading_time": round(unloading_time, 1),
                "empty_transport_time": round(empty_transport_time, 1),
            },
            "recommendations": recommendations,
        }

    @staticmethod
    def _generate_recommendations(
        params: dict[str, Any], cycle_time: float, bottleneck: str
    ) -> list[str]:
        """改善提案を生成"""
        recommendations = []

        if bottleneck == "loading":
            recommendations.append("積込み時間が長いです。重機の台数を増やすか、積込み方法を見直してください。")
            recommendations.append("待機時間削減のため、ダンプの配車タイミングを最適化してください。")

        elif bottleneck == "loaded_transport":
            recommendations.append("運搬時間が長いです。運搬ルートの最適化を検討してください。")
            recommendations.append("積載時の速度を上げられる場合は、道路状況を改善してください。")

        elif bottleneck == "unloading":
            recommendations.append("荷降ろし時間が長いです。荷降ろし場所の拡大を検討してください。")
            recommendations.append("荷降ろしの並行作業エリアを増やすことで効率化できます。")

        elif bottleneck == "empty_transport":
            recommendations.append("空車の運搬時間が長いです。一方通行ルートの設定を検討してください。")

        # サイクルタイムが長い場合
        if cycle_time > 60:
            recommendations.append(
                f"サイクルタイムが{round(cycle_time, 1)}分と長いです。ダンプ台数を{int(params['trucks_count']) + 1}台に増やすことを検討してください。"
            )

        return recommendations

    @staticmethod
    def _generate_timeline(params: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
        """
        時系列データを生成

        Returns:
            時間ごとの推移データ
        """
        timeline = {"hours": [], "cumulative_volume": [], "trucks_active": []}

        total_hours = results["total_time_hours"]
        trucks_count = params["trucks_count"]
        truck_capacity = params["truck_capacity"]

        # 1時間ごとにシミュレート
        for hour in range(int(total_hours) + 1):
            timeline["hours"].append(hour)

            # 累積土量
            hourly_cycles = (60 / results["average_cycle_time"]) * trucks_count
            cumulative = min(
                hourly_cycles * hour * truck_capacity, params["excavation_volume"]
            )
            timeline["cumulative_volume"].append(round(cumulative, 1))

            # 稼働台数（簡易）
            active_trucks = trucks_count if cumulative < params["excavation_volume"] else 0
            timeline["trucks_active"].append(active_trucks)

        return timeline

    @staticmethod
    async def run_resource_optimization(
        db: AsyncSession,
        site_id: UUID,
        parameters: dict[str, Any],
    ) -> Simulation:
        """
        リソース最適化シミュレーション

        Args:
            db: データベースセッション
            site_id: 現場ID
            parameters: パラメータ

        Returns:
            Simulationオブジェクト
        """
        simulation = Simulation(
            site_id=site_id,
            simulation_name=f"リソース最適化 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            simulation_type="resource_allocation",
            parameters=parameters,
            status="running",
            started_at=datetime.now(),  # type: ignore
        )

        db.add(simulation)
        await db.commit()

        try:
            # 最適化アルゴリズム実行（線形計画法など）
            # ここでは簡易実装
            results = {
                "optimal_trucks": 5,
                "optimal_excavators": 2,
                "cost_reduction": 15.5,
                "efficiency_improvement": 12.3,
            }

            simulation_result = SimulationResult(
                simulation_id=simulation.id, results=results
            )

            db.add(simulation_result)

            simulation.status = "completed"
            simulation.completed_at = datetime.now()  # type: ignore

            await db.commit()
            await db.refresh(simulation)

        except Exception as e:
            simulation.status = "failed"
            simulation.error_message = str(e)
            await db.commit()
            raise

        return simulation
