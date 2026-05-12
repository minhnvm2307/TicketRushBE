from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ExpiredEventError
from app.core.redis import RedisKey, dumps_payload, get_redis_client, loads_payload, redis_is_enabled
from app.models.enums import InteractionType, SeatStatus, ZoneType
from app.models.interaction import UserEventInteraction
from app.models.seat import Seat, SeatZone
from app.repositories.event import EventRepository
from app.repositories.interaction import InteractionRepository
from app.repositories.order import OrderRepository
from app.repositories.seat import SeatRepository
from app.schemas.seat import SeatMapResponse, SeatMapZoneResponse
from app.services.dashboard import DashboardService
from app.services.realtime import connection_manager


class SeatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.seats = SeatRepository(db)
        self.events = EventRepository(db)
        self.interactions = InteractionRepository(db)
        self.settings = get_settings()
        self.redis = get_redis_client() if redis_is_enabled() else None

    def get_seat_map(self, event_id: str) -> SeatMapResponse:
        self._require_active_event(event_id)
        zones = self.seats.list_by_event(event_id)
        zone_responses = [SeatMapZoneResponse.model_validate(zone) for zone in zones]
        return SeatMapResponse(event_id=event_id, zones=zone_responses)

    def _require_active_event(self, event_id: str) -> None:
        if not self.events.get_public_active_by_id(event_id):
            raise ExpiredEventError("event has ended or is unavailable")

    def _has_queue_access(self, event_id: str, user_id: str) -> bool:
        if not self.redis:
            return False
        access_key = RedisKey.event_access_token(event_id, user_id)
        return self.redis.ttl(access_key) > 0

    def _has_checkout_access(self, event_id: str, user_id: str) -> bool:
        if not self.redis:
            return False
        return self.redis.ttl(RedisKey.checkout_access(str(event_id), str(user_id))) > 0

    def _session_ttl(self, session_id: str | None, user_id: str) -> int | None:
        if not self.redis or not session_id:
            return None
        session_user_id = self.redis.get(RedisKey.auth_session(session_id))
        if session_user_id != str(user_id):
            raise ValueError("Session has expired. Please sign in again.")
        ttl = self.redis.ttl(RedisKey.auth_session(session_id))
        return ttl if ttl and ttl > 0 else None

    def _user_hold_index_key(self, user_id: str, event_id: str) -> str:
        return RedisKey.user_event_hold_index(str(user_id), str(event_id))

    def _active_hold_count(self, user_id: str, event_id: str, now: datetime) -> int:
        if not self.redis:
            return 0
        hold_index_key = self._user_hold_index_key(user_id, event_id)
        self.redis.zremrangebyscore(hold_index_key, "-inf", now.timestamp())
        return int(self.redis.zcard(hold_index_key))

    def _sync_checkout_lease(self, user_id: str, event_id: str, session_ttl: int | None = None) -> None:
        if not self.redis:
            return
        hold_index_key = self._user_hold_index_key(user_id, event_id)
        now_ts = datetime.now(UTC).timestamp()
        self.redis.zremrangebyscore(hold_index_key, "-inf", now_ts)
        checkout_key = RedisKey.checkout_access(str(event_id), str(user_id))
        latest = self.redis.zrange(hold_index_key, -1, -1, withscores=True)
        if not latest:
            self.redis.delete(checkout_key)
            return
        _member, expiry_ts = latest[0]
        ttl_seconds = max(1, int(expiry_ts - now_ts))
        if session_ttl is not None:
            ttl_seconds = min(ttl_seconds, session_ttl)
        if ttl_seconds <= 0:
            self.redis.delete(checkout_key)
            return
        self.redis.set(checkout_key, "1", ex=ttl_seconds)

    def _max_bookable_for_event(self, event) -> int:
        return int(getattr(event, "max_bookable", None) or self.settings.default_max_bookable_per_user)

    def _enforce_max_bookable(self, event, user_id: str, requested_count: int, now: datetime) -> None:
        current_holds = self._active_hold_count(user_id, str(event.id), now)
        tickets_bought = OrderRepository(self.db).count_tickets_by_user_event(user_id, str(event.id))
        max_bookable = self._max_bookable_for_event(event)
        if current_holds + tickets_bought + requested_count > max_bookable:
            raise ValueError(f"You can only purchase up to {max_bookable} tickets for this event.")

    async def hold(self, seat_id: str, user_id: str, event_id: str, session_id: str | None = None) -> dict:
        if not self.redis:
            raise ConnectionError("Redis is not enabled or connected")
        event = self.events.get_public_active_by_id(event_id)
        if not event:
            raise ExpiredEventError("event has ended or is unavailable")
        if not self._has_queue_access(event_id, user_id):
            raise ValueError("Please wait in the queue before holding seats.")

        now = datetime.now(UTC)
        self._enforce_max_bookable(event, user_id, requested_count=1, now=now)
        session_ttl = self._session_ttl(session_id, user_id)
        hold_seconds = self.settings.hold_ttl_seconds
        if session_ttl is not None:
            hold_seconds = min(hold_seconds, session_ttl)
        if hold_seconds <= 0:
            raise ValueError("Session has expired. Please sign in again.")
        locked_until = now + timedelta(seconds=hold_seconds)
        lock_key = RedisKey.seat_lock(event_id, seat_id)
        lock_payload = dumps_payload({"user_id": user_id, "locked_until": locked_until.isoformat()})

        if not self.redis.set(lock_key, lock_payload, ex=hold_seconds, nx=True):
            raise ValueError("Seat is already held by another user.")

        try:
            with self.db.begin_nested():
                self.seats.release_expired_holds(now)
                seat = self.seats.get_by_id_for_update(seat_id)
                if not seat or str(seat.zone.event_id) != str(event_id):
                    raise ValueError("Seat not found for this event.")
                if seat.zone.zone_type != ZoneType.ASSIGNED:
                    raise ValueError("Seat holds are only supported for assigned seating.")
                if seat.status == SeatStatus.SOLD:
                    raise ValueError("Seat is already sold.")
                if seat.status == SeatStatus.LOCKED:
                    if str(seat.locked_by) == str(user_id) and seat.locked_until and seat.locked_until > now:
                        seat.locked_until = locked_until
                    else:
                        raise ValueError("Seat is already held by another user.")

                seat.status = SeatStatus.LOCKED
                seat.locked_by = user_id
                seat.locked_until = locked_until

                self.interactions.add(
                    UserEventInteraction(user_id=user_id, event_id=event_id, interaction_type=InteractionType.HOLD)
                )
            self.db.commit()
            hold_index_key = self._user_hold_index_key(user_id, event_id)
            self.redis.zadd(hold_index_key, {str(seat_id): locked_until.timestamp()})
            self.redis.expire(hold_index_key, hold_seconds)
            self._sync_checkout_lease(user_id, event_id, session_ttl=session_ttl)
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
            self.redis.delete(lock_key)
            self.db.rollback()
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

        try:
            with self.db.begin_nested():
                seat = self.seats.get_by_id_for_update(seat_id)
                if not seat or str(seat.zone.event_id) != str(event_id):
                    raise ValueError("Seat not found for this event.")
                if str(seat.locked_by) != str(user_id):
                    raise ValueError("Seat is not held by the current user.")

                seat.status = SeatStatus.AVAILABLE
                seat.locked_by = None
                seat.locked_until = None
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.redis.delete(lock_key)
        self.redis.zrem(self._user_hold_index_key(user_id, event_id), str(seat_id))
        self._sync_checkout_lease(user_id, event_id)

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
            zone_type=getattr(payload, "zone_type", ZoneType.ASSIGNED),
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
    
    @staticmethod
    def serialize_zone(zone: SeatZone) -> dict:
        return {
            "id": zone.id,
            "name": zone.name,
            "zone_type": zone.zone_type.value,
            "rows": zone.rows,
            "cols": zone.cols,
            "price": float(zone.price),
            "capacity": zone.capacity,
            "color": zone.color,
            "seats": [SeatService.serialize_seat(seat) for seat in zone.seats]
        }
    
    @staticmethod
    def serialize_seat(seat: Seat) -> dict:
        return {
            "id": seat.id,
            "label": seat.label,
            "row_index": seat.row_index,
            "col_index": seat.col_index,
            "status": seat.status.value,
            "locked_by": str(seat.locked_by) if seat.locked_by else None,
            "locked_until": seat.locked_until.isoformat() if seat.locked_until else None
        }
