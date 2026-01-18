"""
GPS端末連携サービス
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import GPSPosition, Vehicle


class GPSService:
    """GPS端末連携サービス"""

    @staticmethod
    async def receive_gps_data(
        db: AsyncSession,
        raw_data: dict[str, Any],
        device_type: str = "generic",
    ) -> Optional[GPSPosition]:
        """
        GPS端末からデータを受信して正規化

        Args:
            db: データベースセッション
            raw_data: GPS端末からの生データ
            device_type: デバイスタイプ ('gpsnext', 'trackimo', 'smartphone')

        Returns:
            保存されたGPSPositionオブジェクト、またはNone
        """
        # デバイスタイプに応じてデータを正規化
        normalized = await GPSService._normalize_gps_data(raw_data, device_type)

        if not normalized:
            return None

        # 車両IDからVehicleを検索
        stmt = select(Vehicle).where(Vehicle.gps_device_id == normalized["device_id"])
        result = await db.execute(stmt)
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            print(f"⚠️ GPS device {normalized['device_id']} not registered")
            return None

        # GPS位置データを作成
        gps_position = GPSPosition(
            time=normalized["timestamp"],
            vehicle_id=vehicle.id,
            location=WKTElement(
                f"POINT({normalized['longitude']} {normalized['latitude']})",
                srid=4326,
            ),
            latitude=normalized["latitude"],
            longitude=normalized["longitude"],
            altitude=normalized.get("altitude"),
            speed=normalized.get("speed"),
            heading=normalized.get("heading"),
            accuracy=normalized.get("accuracy"),
            device_id=normalized["device_id"],
            battery_level=normalized.get("battery_level"),
            estimated_state=await GPSService._estimate_vehicle_state(
                db, vehicle.id, normalized
            ),
            raw_data=raw_data,
        )

        db.add(gps_position)
        await db.commit()
        await db.refresh(gps_position)

        return gps_position

    @staticmethod
    async def _normalize_gps_data(
        raw_data: dict[str, Any], device_type: str
    ) -> Optional[dict[str, Any]]:
        """
        デバイスタイプ別にGPSデータを正規化

        Args:
            raw_data: 生データ
            device_type: デバイスタイプ

        Returns:
            正規化されたデータ
        """
        try:
            if device_type == "gpsnext":
                return GPSService._normalize_gpsnext(raw_data)
            elif device_type == "trackimo":
                return GPSService._normalize_trackimo(raw_data)
            elif device_type == "smartphone":
                return GPSService._normalize_smartphone(raw_data)
            else:
                # 汎用フォーマット
                return {
                    "device_id": raw_data.get("device_id"),
                    "timestamp": datetime.fromisoformat(
                        raw_data.get("timestamp", datetime.utcnow().isoformat())
                    ),
                    "latitude": float(raw_data["latitude"]),
                    "longitude": float(raw_data["longitude"]),
                    "altitude": raw_data.get("altitude"),
                    "speed": raw_data.get("speed"),
                    "heading": raw_data.get("heading"),
                    "accuracy": raw_data.get("accuracy"),
                    "battery_level": raw_data.get("battery_level"),
                }
        except (KeyError, ValueError, TypeError) as e:
            print(f"❌ GPS data normalization failed: {e}")
            return None

    @staticmethod
    def _normalize_gpsnext(raw_data: dict[str, Any]) -> dict[str, Any]:
        """GPSnext形式のデータを正規化"""
        return {
            "device_id": raw_data["imei"],
            "timestamp": datetime.fromisoformat(raw_data["timestamp"]),
            "latitude": float(raw_data["lat"]),
            "longitude": float(raw_data["lon"]),
            "altitude": raw_data.get("alt"),
            "speed": raw_data.get("speed"),
            "heading": raw_data.get("course"),
            "accuracy": raw_data.get("hdop"),
            "battery_level": raw_data.get("battery"),
        }

    @staticmethod
    def _normalize_trackimo(raw_data: dict[str, Any]) -> dict[str, Any]:
        """Trackimo形式のデータを正規化"""
        return {
            "device_id": raw_data["device_id"],
            "timestamp": datetime.fromtimestamp(raw_data["timestamp"]),
            "latitude": float(raw_data["latitude"]),
            "longitude": float(raw_data["longitude"]),
            "altitude": raw_data.get("altitude"),
            "speed": raw_data.get("speed_kmh"),
            "heading": raw_data.get("direction"),
            "accuracy": raw_data.get("accuracy_m"),
            "battery_level": raw_data.get("battery_percent"),
        }

    @staticmethod
    def _normalize_smartphone(raw_data: dict[str, Any]) -> dict[str, Any]:
        """スマートフォン形式のデータを正規化"""
        coords = raw_data["coords"]
        return {
            "device_id": raw_data["device_id"],
            "timestamp": datetime.fromtimestamp(raw_data["timestamp"] / 1000),
            "latitude": float(coords["latitude"]),
            "longitude": float(coords["longitude"]),
            "altitude": coords.get("altitude"),
            "speed": coords.get("speed"),
            "heading": coords.get("heading"),
            "accuracy": coords.get("accuracy"),
            "battery_level": raw_data.get("battery", {}).get("level"),
        }

    @staticmethod
    async def _estimate_vehicle_state(
        db: AsyncSession, vehicle_id: UUID, gps_data: dict[str, Any]
    ) -> Optional[str]:
        """
        GPS位置データから車両の状態を推定

        Args:
            db: データベースセッション
            vehicle_id: 車両ID
            gps_data: GPSデータ

        Returns:
            推定された状態
            'loading', 'loaded_moving', 'unloading', 'empty_moving', 'idle'
        """
        speed = gps_data.get("speed", 0)

        # 速度ベースの簡易判定
        if speed < 1:
            return "idle"
        elif speed < 10:
            # 低速 → 積込み中または荷降ろし中の可能性
            # TODO: ジオフェンスとの照合で詳細判定
            return "loading"
        else:
            # 走行中
            # TODO: 前回の状態から積載/空車を判定
            return "loaded_moving"

    @staticmethod
    async def get_vehicle_latest_position(
        db: AsyncSession, vehicle_id: UUID
    ) -> Optional[GPSPosition]:
        """
        車両の最新位置を取得

        Args:
            db: データベースセッション
            vehicle_id: 車両ID

        Returns:
            最新のGPSPosition、またはNone
        """
        stmt = (
            select(GPSPosition)
            .where(GPSPosition.vehicle_id == vehicle_id)
            .order_by(GPSPosition.time.desc())
            .limit(1)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_vehicle_track(
        db: AsyncSession,
        vehicle_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> list[GPSPosition]:
        """
        車両の移動軌跡を取得

        Args:
            db: データベースセッション
            vehicle_id: 車両ID
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            GPS位置データのリスト
        """
        stmt = (
            select(GPSPosition)
            .where(
                GPSPosition.vehicle_id == vehicle_id,
                GPSPosition.time >= start_time,
                GPSPosition.time <= end_time,
            )
            .order_by(GPSPosition.time)
        )

        result = await db.execute(stmt)
        return list(result.scalars().all())
