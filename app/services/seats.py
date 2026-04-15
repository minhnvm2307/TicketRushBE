from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import dumps_payload, get_redis_client, loads_payload, redis_is_enabled
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

    def _seat_hold_key(self, seat_id: str) -> str:
        return f"seat_hold:{seat_id}"

    def get_seat_map(self, event_id: str) -> SeatMapResponse:
        zones = self.seats.list_by_event(event_id)
        return SeatMapResponse(event_id=event_id, zones=[SeatMapZoneResponse.model_validate(zone) for zone in zones])

    async def hold(self, seat_id: str, user_id: str) -> datetime:
        now = datetime.now(UTC)
        hold_seconds = self.settings.hold_duration_minutes * 60
        hold_key = self._seat_hold_key(seat_id)
        acquired_new_key = False

        if self.redis:
            existing_hold = loads_payload(self.redis.get(hold_key))
            if existing_hold and existing_hold.get("user_id") != user_id:
                raise ValueError("seat just taken, please choose another")
            if not existing_hold:
                acquired_new_key = bool(
                    self.redis.set(hold_key, dumps_payload({"user_id": user_id}), ex=hold_seconds, nx=True)
                )
                if not acquired_new_key:
                    raise ValueError("seat just taken, please choose another")

        seat = self.seats.get_by_id_for_update(seat_id)
        if not seat:
            if self.redis and acquired_new_key:
                self.redis.delete(hold_key)
            raise ValueError("seat not found")

        if seat.status == SeatStatus.SOLD:
            if self.redis and acquired_new_key:
                self.redis.delete(hold_key)
            raise ValueError("seat already sold")
        if seat.status == SeatStatus.LOCKED and seat.locked_by != user_id and seat.locked_until and seat.locked_until > now:
            if self.redis and acquired_new_key:
                self.redis.delete(hold_key)
            raise ValueError("seat just taken, please choose another")

        locked_until = now + timedelta(minutes=self.settings.hold_duration_minutes)
        seat.status = SeatStatus.LOCKED
        seat.locked_by = user_id
        seat.locked_until = locked_until
        self.interactions.add(
            UserEventInteraction(user_id=user_id, event_id=seat.zone.event_id, interaction_type=InteractionType.HOLD)
        )
        self.db.commit()
        if self.redis:
            self.redis.set(
                hold_key,
                dumps_payload(
                    {"user_id": user_id, "event_id": seat.zone.event_id, "locked_until": locked_until.isoformat()}
                ),
                ex=hold_seconds,
            )
        await connection_manager.broadcast(
            seat.zone.event_id,
            {
                "type": "seat_status_changed",
                "seat_id": seat.id,
                "status": SeatStatus.LOCKED.value,
                "locked_by": user_id,
                "locked_until": locked_until.isoformat(),
            },
        )
        await DashboardService(self.db).broadcast_dashboard_update(seat.zone.event_id)
        return locked_until

    async def release(self, seat_id: str, user_id: str) -> None:
        seat = self.seats.get_by_id_for_update(seat_id)
        if not seat:
            raise ValueError("seat not found")
        if seat.locked_by != user_id:
            raise ValueError("seat is not held by current user")
        seat.status = SeatStatus.AVAILABLE
        seat.locked_by = None
        seat.locked_until = None
        self.db.commit()
        if self.redis:
            self.redis.delete(self._seat_hold_key(seat_id))
        await connection_manager.broadcast(
            seat.zone.event_id,
            {
                "type": "seat_status_changed",
                "seat_id": seat.id,
                "status": SeatStatus.AVAILABLE.value,
                "locked_by": None,
            },
        )
        await DashboardService(self.db).broadcast_dashboard_update(seat.zone.event_id)

    async def release_expired(self) -> list[str]:
        released_ids = self.seats.release_expired()
        self.db.commit()
        if self.redis:
            for seat_id in released_ids:
                self.redis.delete(self._seat_hold_key(seat_id))
        return released_ids

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
