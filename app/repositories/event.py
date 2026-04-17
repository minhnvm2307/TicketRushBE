from datetime import datetime
from app.services.embedding import generate_embedding

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event, EventCategory, EventTag
from app.models.enums import EventStatus, SeatStatus
from app.models.seat import Seat, SeatZone


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_published(
        self, search: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> list[tuple[Event, float | None]]:
        cosine_distance = None

        stmt = (
            select(Event)
            .where(Event.status == EventStatus.PUBLISHED, Event.is_private.is_(False))
            .options(joinedload(Event.categories), joinedload(Event.tags), joinedload(Event.zones))
        )

        if search:
            search_embedding = generate_embedding(search)
            cosine_distance = Event.embedding.cosine_distance(search_embedding).label("cosine_distance")
            stmt = stmt.add_columns(cosine_distance).order_by(cosine_distance.asc())
        else:
            stmt = stmt.order_by(Event.start_time.asc())

        if date_from:
            stmt = stmt.where(Event.start_time >= date_from)
        if date_to:
            stmt = stmt.where(Event.start_time <= date_to)

        if cosine_distance is None:
            events = list(self.db.scalars(stmt).unique().all())
            return [(event, None) for event in events]

        rows = self.db.execute(stmt).unique().all()
        return [(event, float(distance) if distance is not None else None) for event, distance in rows]

    def list_recommendable(self) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.status == EventStatus.PUBLISHED)
            .options(joinedload(Event.categories), joinedload(Event.tags))
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_public_missing_embeddings(self) -> list[Event]:
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.is_private.is_(False),
            Event.embedding.is_(None),
        )
        return list(self.db.scalars(stmt).all())

    def list_public_published(self) -> list[Event]:
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.is_private.is_(False),
        )
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, event_id: str) -> Event | None:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                joinedload(Event.categories),
                joinedload(Event.tags),
                joinedload(Event.zones).joinedload(SeatZone.seats),
            )
        )
        return self.db.scalar(stmt)

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()
        return event

    def delete_categories_and_tags(self, event_id: str) -> None:
        self.db.query(EventCategory).filter(EventCategory.event_id == event_id).delete()
        self.db.query(EventTag).filter(EventTag.event_id == event_id).delete()

    def find_lowest_price(self, event_id: str) -> float | None:
        return self.db.scalar(select(func.min(SeatZone.price)).where(SeatZone.event_id == event_id))

    def has_sold_seats(self, event_id: str) -> bool:
        stmt = (
            select(func.count(Seat.id))
            .join(SeatZone, Seat.zone_id == SeatZone.id)
            .where(SeatZone.event_id == event_id, Seat.status == SeatStatus.SOLD)
        )
        return bool(self.db.scalar(stmt))

    def list_active_for_queue_processing(self) -> list[Event]:
        """
        Returns a list of active, published events that have not ended yet.
        This is used by the queue processing worker.
        """
        now = datetime.now()
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.end_time > now,
            Event.deleted_at.is_(None)
        )
        return list(self.db.scalars(stmt).all())
