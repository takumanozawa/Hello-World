"""
運搬サイクルタイム計測サービス
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_DWithin, ST_Distance
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.vehicle import Geofence, GPSPosition, Vehicle, VehicleCycle


class CycleService:
    """運搬サイクルタイム計測サービス"""

    @staticmethod
    async def detect_and_create_cycle(
        db: AsyncSession,
        vehicle_id: UUID,
        gps_positions: list[GPSPosition],
    ) -> Optional[VehicleCycle]:
        """
        GPS位置データから運搬サイクルを検出・作成

        Args:
            db: データベースセッション
            vehicle_id: 車両ID
            gps_positions: GPS位置データのリスト（時系列順）

        Returns:
            作成されたVehicleCycle、またはNone
        """
        if len(gps_positions) < 10:
            # データ不足
            return None

        # 車両情報取得
        vehicle = await db.get(Vehicle, vehicle_id)
        if not vehicle or not vehicle.current_site_id:
            return None

        # ジオフェンス取得
        loading_zone = await CycleService._get_geofence(
            db, vehicle.current_site_id, "loading_zone"
        )
        unloading_zone = await CycleService._get_geofence(
            db, vehicle.current_site_id, "unloading_zone"
        )

        if not loading_zone or not unloading_zone:
            print(f"⚠️ Geofences not configured for site {vehicle.current_site_id}")
            return None

        # サイクル検出
        cycle_data = await CycleService._analyze_cycle_from_positions(
            db, gps_positions, loading_zone, unloading_zone
        )

        if not cycle_data:
            return None

        # 当日の連番取得
        cycle_number = await CycleService._get_next_cycle_number(
            db, vehicle_id, cycle_data["cycle_date"]
        )

        # VehicleCycle作成
        cycle = VehicleCycle(
            vehicle_id=vehicle_id,
            site_id=vehicle.current_site_id,
            cycle_date=cycle_data["cycle_date"],
            cycle_number=cycle_number,
            start_time=cycle_data["start_time"],
            end_time=cycle_data.get("end_time"),
            total_duration=cycle_data.get("total_duration"),
            loading_location=cycle_data.get("loading_location"),
            loading_start=cycle_data.get("loading_start"),
            loading_end=cycle_data.get("loading_end"),
            loading_duration=cycle_data.get("loading_duration"),
            loaded_moving_start=cycle_data.get("loaded_moving_start"),
            loaded_moving_end=cycle_data.get("loaded_moving_end"),
            loaded_duration=cycle_data.get("loaded_duration"),
            loaded_distance=cycle_data.get("loaded_distance"),
            unloading_location=cycle_data.get("unloading_location"),
            unloading_start=cycle_data.get("unloading_start"),
            unloading_end=cycle_data.get("unloading_end"),
            unloading_duration=cycle_data.get("unloading_duration"),
            empty_moving_start=cycle_data.get("empty_moving_start"),
            empty_moving_end=cycle_data.get("empty_moving_end"),
            empty_duration=cycle_data.get("empty_duration"),
            empty_distance=cycle_data.get("empty_distance"),
            waiting_duration=cycle_data.get("waiting_duration"),
            volume=cycle_data.get("volume", vehicle.capacity),
            status="completed" if cycle_data.get("end_time") else "in_progress",
        )

        db.add(cycle)
        await db.commit()
        await db.refresh(cycle)

        return cycle

    @staticmethod
    async def _get_geofence(
        db: AsyncSession, site_id: UUID, fence_type: str
    ) -> Optional[Geofence]:
        """ジオフェンスを取得"""
        stmt = select(Geofence).where(
            and_(
                Geofence.site_id == site_id,
                Geofence.fence_type == fence_type,
                Geofence.is_active == "True",
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def _analyze_cycle_from_positions(
        db: AsyncSession,
        positions: list[GPSPosition],
        loading_zone: Geofence,
        unloading_zone: Geofence,
    ) -> Optional[dict]:
        """
        GPS位置データからサイクル情報を分析

        Args:
            db: データベースセッション
            positions: GPS位置データ（時系列順）
            loading_zone: 積込みゾーン
            unloading_zone: 荷降ろしゾーン

        Returns:
            サイクル情報の辞書
        """
        cycle_data: dict = {
            "cycle_date": positions[0].time.date(),
            "start_time": positions[0].time,
        }

        # 状態遷移を検出
        states: list[dict] = []
        current_state = None
        state_start_time = None
        state_start_pos = None

        for pos in positions:
            # 位置から状態を判定
            in_loading = await CycleService._is_in_zone(db, pos, loading_zone)
            in_unloading = await CycleService._is_in_zone(db, pos, unloading_zone)

            new_state = None
            if in_loading and (pos.speed or 0) < 5:
                new_state = "loading"
            elif in_unloading and (pos.speed or 0) < 5:
                new_state = "unloading"
            elif (pos.speed or 0) > 10:
                # 推定: 前回が積込みなら積載移動、荷降ろしなら空車移動
                if current_state == "loading":
                    new_state = "loaded_moving"
                elif current_state == "unloading":
                    new_state = "empty_moving"

            # 状態変化を検出
            if new_state != current_state:
                if current_state:
                    states.append(
                        {
                            "state": current_state,
                            "start_time": state_start_time,
                            "end_time": pos.time,
                            "duration": pos.time - state_start_time,  # type: ignore
                            "start_pos": state_start_pos,
                            "end_pos": pos,
                        }
                    )

                current_state = new_state
                state_start_time = pos.time
                state_start_pos = pos

        # 最後の状態を追加
        if current_state:
            states.append(
                {
                    "state": current_state,
                    "start_time": state_start_time,
                    "end_time": positions[-1].time,
                    "duration": positions[-1].time - state_start_time,  # type: ignore
                    "start_pos": state_start_pos,
                    "end_pos": positions[-1],
                }
            )

        # サイクルデータを構築
        for state in states:
            if state["state"] == "loading":
                cycle_data["loading_start"] = state["start_time"]
                cycle_data["loading_end"] = state["end_time"]
                cycle_data["loading_duration"] = state["duration"]
                cycle_data["loading_location"] = state["start_pos"].location

            elif state["state"] == "loaded_moving":
                cycle_data["loaded_moving_start"] = state["start_time"]
                cycle_data["loaded_moving_end"] = state["end_time"]
                cycle_data["loaded_duration"] = state["duration"]
                cycle_data["loaded_distance"] = await CycleService._calculate_distance(
                    state["start_pos"], state["end_pos"]
                )

            elif state["state"] == "unloading":
                cycle_data["unloading_start"] = state["start_time"]
                cycle_data["unloading_end"] = state["end_time"]
                cycle_data["unloading_duration"] = state["duration"]
                cycle_data["unloading_location"] = state["start_pos"].location

            elif state["state"] == "empty_moving":
                cycle_data["empty_moving_start"] = state["start_time"]
                cycle_data["empty_moving_end"] = state["end_time"]
                cycle_data["empty_duration"] = state["duration"]
                cycle_data["empty_distance"] = await CycleService._calculate_distance(
                    state["start_pos"], state["end_pos"]
                )

        # サイクル完了判定
        if "loading_start" in cycle_data and "unloading_end" in cycle_data:
            cycle_data["end_time"] = cycle_data["unloading_end"]
            cycle_data["total_duration"] = (
                cycle_data["end_time"] - cycle_data["start_time"]
            )
            return cycle_data
        elif "loading_start" in cycle_data:
            # 進行中のサイクル
            return cycle_data
        else:
            # サイクルとして不完全
            return None

    @staticmethod
    async def _is_in_zone(
        db: AsyncSession, position: GPSPosition, zone: Geofence
    ) -> bool:
        """位置がジオフェンス内かを判定"""
        # PostGIS ST_Within を使用
        # ここでは簡易的に実装
        # 実際にはST_Withinクエリを実行
        return False  # TODO: 実装

    @staticmethod
    async def _calculate_distance(pos1: GPSPosition, pos2: GPSPosition) -> Decimal:
        """2点間の距離を計算（km）"""
        # Haversine formula
        from math import asin, cos, radians, sin, sqrt

        lat1, lon1 = float(pos1.latitude), float(pos1.longitude)
        lat2, lon2 = float(pos2.latitude), float(pos2.longitude)

        # 地球の半径 (km)
        R = 6371.0

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        )
        c = 2 * asin(sqrt(a))
        distance = R * c

        return Decimal(str(round(distance, 2)))

    @staticmethod
    async def _get_next_cycle_number(
        db: AsyncSession, vehicle_id: UUID, cycle_date: datetime
    ) -> int:
        """当日の次のサイクル番号を取得"""
        stmt = (
            select(VehicleCycle)
            .where(
                and_(
                    VehicleCycle.vehicle_id == vehicle_id,
                    VehicleCycle.cycle_date == cycle_date,
                )
            )
            .order_by(VehicleCycle.cycle_number.desc())
            .limit(1)
        )

        result = await db.execute(stmt)
        last_cycle = result.scalar_one_or_none()

        if last_cycle:
            return last_cycle.cycle_number + 1
        else:
            return 1

    @staticmethod
    async def get_daily_cycle_statistics(
        db: AsyncSession, vehicle_id: UUID, target_date: datetime
    ) -> dict:
        """
        車両の日別サイクル統計を取得

        Args:
            db: データベースセッション
            vehicle_id: 車両ID
            target_date: 対象日

        Returns:
            統計情報の辞書
        """
        stmt = select(VehicleCycle).where(
            and_(
                VehicleCycle.vehicle_id == vehicle_id,
                VehicleCycle.cycle_date == target_date.date(),
                VehicleCycle.status == "completed",
            )
        )

        result = await db.execute(stmt)
        cycles = list(result.scalars().all())

        if not cycles:
            return {
                "total_cycles": 0,
                "total_volume": 0,
                "average_cycle_time": 0,
                "average_loading_time": 0,
                "average_unloading_time": 0,
                "total_distance": 0,
            }

        total_cycles = len(cycles)
        total_volume = sum(c.volume or 0 for c in cycles)
        total_cycle_time = sum(
            (c.total_duration.total_seconds() if c.total_duration else 0) for c in cycles
        )
        total_loading_time = sum(
            (c.loading_duration.total_seconds() if c.loading_duration else 0)
            for c in cycles
        )
        total_unloading_time = sum(
            (c.unloading_duration.total_seconds() if c.unloading_duration else 0)
            for c in cycles
        )
        total_distance = sum((c.loaded_distance or 0) + (c.empty_distance or 0) for c in cycles)

        return {
            "total_cycles": total_cycles,
            "total_volume": float(total_volume),
            "average_cycle_time": total_cycle_time / total_cycles / 60,  # 分
            "average_loading_time": total_loading_time / total_cycles / 60,  # 分
            "average_unloading_time": total_unloading_time / total_cycles / 60,  # 分
            "total_distance": float(total_distance),
        }
