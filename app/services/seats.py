from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import RedisKey, dumps_payload, get_redis_client, loads_payload, redis_is_enabled
from app.models.enums import InteractionType, SeatStatus
from app.models.interaction import UserEventInteraction
from app.models.seat import Seat, SeatZone
from app.repositories.interaction import InteractionRepository
from app.repositories.seat import SeatRepository
from app.schemas.seat import SeatMapResponse, SeatMapZoneResponse
from app.services.dashboard import DashboardService
from app.services.realtime import connection_manager


class SeatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.seats = SeatRepository(db)
        self.interactions = InteractionRepository(db)
        self.settings = get_settings()
        self.redis = get_redis_client() if redis_is_enabled() else None

    def get_seat_map(self, event_id: str) -> SeatMapResponse:
        # Step 1: Fetch all structural seats from PostgreSQL
        zones = self.seats.list_by_event(event_id)
        zone_responses = [SeatMapZoneResponse.model_validate(zone) for zone in zones]

        if not self.redis:
            return SeatMapResponse(event_id=event_id, zones=zone_responses)

        # Step 2: Fetch all active Redis locks for this event
        lock_keys = self.redis.scan_iter(RedisKey.seat_lock(event_id, "*"))
        active_locks = self.redis.mget(lock_keys)

        lock_details = {}
        for key, lock_json in zip(lock_keys, active_locks):
            if lock_json:
                seat_id = key.split(":")[-2]
                lock_details[seat_id] = loads_payload(lock_json)

        # Step 3: Merge Redis state into the response
        for zone in zone_responses:
            for seat in zone.seats:
                if seat.status == SeatStatus.AVAILABLE and seat.id in lock_details:
                    lock = lock_details[seat.id]
                    seat.status = "LOCKED"
                    seat.locked_by = lock.get("user_id")
                    locked_at = datetime.fromisoformat(lock.get("locked_at"))
                    seat.locked_until = locked_at + timedelta(minutes=self.settings.hold_duration_minutes)

        return SeatMapResponse(event_id=event_id, zones=zone_responses)

    async def hold(self, seat_id: str, user_id: str, event_id: str) -> dict:
        if not self.redis:
            raise ConnectionError("Redis is not enabled or connected")

        now = datetime.now(UTC)
        lock_key = RedisKey.seat_lock(event_id, seat_id)
        lock_payload = dumps_payload({"user_id": user_id, "locked_at": now.isoformat()})
        hold_seconds = self.settings.hold_duration_minutes * 60

        # Use SETNX to acquire the lock atomically
        if not self.redis.set(lock_key, lock_payload, ex=hold_seconds, nx=True):
            raise ValueError("Seat is already held by another user.")

        try:
            seat = self.seats.get_by_id(seat_id)
            if not seat or seat.zone.event_id != event_id:
                raise ValueError("Seat not found for this event.")
            if seat.status == SeatStatus.SOLD:
                raise ValueError("Seat is already sold.")

            # Log interaction
            self.interactions.add(
                UserEventInteraction(user_id=user_id, event_id=event_id, interaction_type=InteractionType.HOLD)
            )
            self.db.commit()

            # Broadcast update to clients
            locked_until = now + timedelta(minutes=self.settings.hold_duration_minutes)
            await connection_manager.broadcast(
                event_id,
                {
                    "type": "seat_status_changed",
                    "seat_id": seat_id,
                    "status": "LOCKED",
                    "locked_by": user_id,
                    "locked_until": locked_until.isoformat(),
                },
            )
            await DashboardService(self.db).broadcast_dashboard_update(event_id)

            return {"seat_id": seat_id, "status": "LOCKED", "locked_until": locked_until.isoformat()}

        except Exception:
            # If any database error occurs, release the Redis lock
            self.redis.delete(lock_key)
            raise

    async def release(self, seat_id: str, user_id: str, event_id: str) -> None:
        if not self.redis:
            raise ConnectionError("Redis is not enabled or connected")

        lock_key = RedisKey.seat_lock(event_id, seat_id)
        lock_data_raw = self.redis.get(lock_key)

        if not lock_data_raw:
            raise ValueError("Seat is not held.")

        lock_data = loads_payload(lock_data_raw)

        if lock_data.get("user_id") != user_id:
            raise ValueError("Seat is not held by the current user.")

        self.redis.delete(lock_key)

        await connection_manager.broadcast(
            event_id,
            {
                "type": "seat_status_changed",
                "seat_id": seat_id,
                "status": "AVAILABLE",
            },
        )
        await DashboardService(self.db).broadcast_dashboard_update(event_id)


    def list_zones(self, event_id: str):
        zones = self.seats.list_by_event(event_id)
        return [SeatMapZoneResponse.model_validate(zone) for zone in zones]

    def create_zone(self, event_id: str, payload) -> SeatZone:
        zone = SeatZone(
            event_id=event_id,
            name=payload.name,
            rows=payload.rows,
            cols=payload.cols,
            price=payload.price,
            capacity=payload.capacity or (payload.rows * payload.cols),
            color=payload.color,
        )
        for row in range(1, payload.rows + 1):
            for col in range(1, payload.cols + 1):
                label = f"{payload.name.upper().replace(' ', '_')}-{chr(64 + row)}{col:02d}"
                zone.seats.append(Seat(label=label, row_index=row - 1, col_index=col - 1))
        self.seats.create_zone(zone)
        self.db.commit()
        self.db.refresh(zone)
        return SeatMapZoneResponse.model_validate(zone)
