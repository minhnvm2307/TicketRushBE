from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import SeatStatus
from app.models.seat import Seat, SeatZone


class SeatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id_for_update(self, seat_id: str) -> Seat | None:
        stmt = select(Seat).where(Seat.id == seat_id).with_for_update()
        return self.db.scalar(stmt)

    def list_held_by_user(self, user_id: str) -> list[Seat]:
        now = datetime.now(UTC)
        stmt = (
            select(Seat)
            .where(Seat.locked_by == user_id, Seat.locked_until.is_not(None), Seat.locked_until > now)
            .options(joinedload(Seat.zone))
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_many_for_update(self, seat_ids: list[str]) -> list[Seat]:
        stmt = select(Seat).where(Seat.id.in_(seat_ids)).with_for_update().options(joinedload(Seat.zone))
        return list(self.db.scalars(stmt).unique().all())

    def count_statuses_by_event(self, event_id: str) -> dict[str, int]:
        stmt = (
            select(Seat.status, func.count(Seat.id))
            .join(SeatZone, Seat.zone_id == SeatZone.id)
            .where(SeatZone.event_id == event_id)
            .group_by(Seat.status)
        )
        rows = self.db.execute(stmt).all()
        return {status.value if isinstance(status, SeatStatus) else status: count for status, count in rows}

    def release_expired(self) -> list[str]:
        now = datetime.now(UTC)
        stmt = select(Seat).where(Seat.status == SeatStatus.LOCKED, Seat.locked_until < now).with_for_update()
        seats = list(self.db.scalars(stmt).all())
        released_ids: list[str] = []
        for seat in seats:
            seat.status = SeatStatus.AVAILABLE
            seat.locked_by = None
            seat.locked_until = None
            released_ids.append(seat.id)
        self.db.flush()
        return released_ids

    def list_by_event(self, event_id: str) -> list[SeatZone]:
        stmt = (
            select(SeatZone)
            .where(SeatZone.event_id == event_id)
            .options(joinedload(SeatZone.seats))
            .order_by(SeatZone.name.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def create_zone(self, zone: SeatZone) -> SeatZone:
        self.db.add(zone)
        self.db.flush()
        return zone
