from datetime import UTC, datetime
from app.services.embedding import generate_embedding

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event
from app.models.enums import EventStatus, SeatStatus
from app.models.seat import Seat, SeatZone

from app.core.config import get_settings


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def list_published(
        self, search: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> list[tuple[Event, float | None]]:
        cosine_distance = None
        now = datetime.now(UTC)

        stmt = (
            select(Event)
            .where(
                Event.status == EventStatus.PUBLISHED,
                Event.is_private.is_(False),
                Event.deleted_at.is_(None),
                Event.end_time > now,
            )
            .options(joinedload(Event.categories), joinedload(Event.zones))
        )

        if search:
            search_embedding = generate_embedding(search)
            cosine_distance = Event.embedding.cosine_distance(search_embedding).label("cosine_distance")
            stmt = stmt.add_columns(cosine_distance).order_by(cosine_distance.asc())
            stmt = stmt.where(cosine_distance <= self.settings.embedding_similarity_threshold * 2)
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
        now = datetime.now(UTC)
        stmt = (
            select(Event)
            .where(
                Event.status == EventStatus.PUBLISHED,
                Event.is_private.is_(False),
                Event.deleted_at.is_(None),
                Event.end_time > now,
            )
            .options(joinedload(Event.categories))
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_public_missing_embeddings(self) -> list[Event]:
        now = datetime.now(UTC)
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.is_private.is_(False),
            Event.deleted_at.is_(None),
            Event.end_time > now,
            Event.embedding.is_(None),
        )
        return list(self.db.scalars(stmt).all())

    def list_public_published(self) -> list[Event]:
        now = datetime.now(UTC)
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.is_private.is_(False),
            Event.deleted_at.is_(None),
            Event.end_time > now,
        )
        return list(self.db.scalars(stmt).all())

    def get_public_active_by_id(self, event_id: str) -> Event | None:
        now = datetime.now(UTC)
        stmt = (
            select(Event)
            .where(
                Event.id == event_id,
                Event.status == EventStatus.PUBLISHED,
                Event.is_private.is_(False),
                Event.deleted_at.is_(None),
                Event.end_time > now,
            )
            .options(
                joinedload(Event.categories),
                joinedload(Event.zones).joinedload(SeatZone.seats),
            )
        )
        return self.db.scalar(stmt)

    def get_by_id(self, event_id: str) -> Event | None:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                joinedload(Event.categories),
                joinedload(Event.zones).joinedload(SeatZone.seats),
            )
        )
        return self.db.scalar(stmt)

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()
        return event

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
        now = datetime.now(UTC)
        stmt = select(Event).where(
            Event.status == EventStatus.PUBLISHED,
            Event.end_time > now,
            Event.deleted_at.is_(None),
        )
        return list(self.db.scalars(stmt).all())
    
    def list_managed_by_host(self, host_id: str) -> list[Event]:
        stmt = select(Event).where(Event.host_id == host_id)
        return list(self.db.scalars(stmt).all())
