from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import SeatStatus, ZoneType
from app.models.seat import Seat, SeatZone


class SeatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, seat_id: str) -> Seat | None:
        return self.db.get(Seat, seat_id)

    def get_by_id_for_update(self, seat_id: str) -> Seat | None:
        stmt = select(Seat).where(Seat.id == seat_id).options(joinedload(Seat.zone))
        return self.db.scalar(stmt)

    def get_many_by_ids(self, seat_ids: list[str]) -> list[Seat]:
        stmt = select(Seat).where(Seat.id.in_(seat_ids)).options(joinedload(Seat.zone))
        return list(self.db.scalars(stmt).unique().all())

    def get_many_by_ids_for_update(self, seat_ids: list[str]) -> list[Seat]:
        stmt = select(Seat).where(Seat.id.in_(seat_ids)).options(joinedload(Seat.zone))
        return list(self.db.scalars(stmt).unique().all())

    def get_general_admission_zone_for_event(self, event_id: str) -> SeatZone | None:
        stmt = (
            select(SeatZone)
            .where(SeatZone.event_id == event_id, SeatZone.zone_type == ZoneType.GENERAL_ADMISSION)
            .order_by(SeatZone.price.asc(), SeatZone.name.asc())
        )
        return self.db.scalar(stmt)

    def count_statuses_by_event(self, event_id: str) -> dict[str, int]:
        stmt = (
            select(Seat.status, func.count(Seat.id))
            .join(SeatZone, Seat.zone_id == SeatZone.id)
            .where(SeatZone.event_id == event_id)
            .group_by(Seat.status)
        )
        rows = self.db.execute(stmt).all()
        return {status.value if isinstance(status, SeatStatus) else status: count for status, count in rows}

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

    def release_expired_holds(self, now: datetime) -> list[Seat]:
        stmt = (
            select(Seat)
            .where(
                Seat.status == SeatStatus.LOCKED,
                Seat.locked_until.is_not(None),
                Seat.locked_until < now,
            )
            .with_for_update()
        )
        seats = list(self.db.scalars(stmt).all())
        for seat in seats:
            seat.status = SeatStatus.AVAILABLE
            seat.locked_by = None
            seat.locked_until = None
        return seats
