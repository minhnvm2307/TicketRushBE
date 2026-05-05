from re import sub

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models.event import Category, Event
from app.models.seat import Seat, SeatZone
from app.repositories.event import EventRepository
from app.schemas.event import CategoryResponse, EventCreateRequest, EventResponse
from app.services.seats import SeatService
from app.services.embedding import generate_embedding



def slugify(value: str) -> str:
    value = sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "event"


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EventRepository(db)

    def list_public(self, search: str | None, date_from, date_to):
        if search:
            self.reindex_public_embeddings(force=False)

        ranked_events = self.repo.list_published(search, date_from, date_to)
        response = []
        for event, cosine_distance in ranked_events:
            similarity_score = None
            if cosine_distance is not None:
                # For cosine distance in [0, 2], convert to a more intuitive similarity score in [0, 1].
                similarity_score = max(0.0, min(1.0, 1.0 - (cosine_distance / 2.0)))

            response.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "slug": event.slug,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "venue": event.venue,
                    "banner_url": event.banner_url,
                    "lowest_price": float(self.repo.find_lowest_price(event.id) or 0),
                    "categories": [CategoryResponse.model_validate(item) for item in event.categories],
                    "cosine_distance": cosine_distance,
                    "similarity_score": similarity_score,
                }
            )

        if search:
            response.sort(key=lambda item: item["cosine_distance"] if item["cosine_distance"] is not None else 1e9)
        return response

    def reindex_public_embeddings(self, force: bool = False) -> int:
        events = self.repo.list_public_published() if force else self.repo.list_public_missing_embeddings()
        if not events:
            return 0

        for event in events:
            event.embedding = generate_embedding(self._build_embedding_text(event.title, event.description))

        self.db.commit()
        return len(events)

    @staticmethod
    def _build_embedding_text(title: str, description: str) -> str:
        # Canonical semantic text for event vectors.
        return f"{title.strip()} {description.strip()}".strip()

    def get_public_detail(self, event_id: str) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        return event
    
    def list_managed_by_host(self, host_id: str) -> list[Event]:
        return self.repo.list_managed_by_host(host_id)

    def create(self, payload: EventCreateRequest, host_id) -> Event:
        event = Event(
            host_id=host_id,
            title=payload.title,
            slug=slugify(payload.title),
            description=payload.description,
            short_description=payload.short_description,
            embedding=generate_embedding(self._build_embedding_text(payload.title, payload.description)),
            start_time=payload.start_time,
            end_time=payload.end_time,
            venue=payload.venue,
            banner_url=payload.banner_url,
            is_private=payload.is_private,
            theme=payload.theme,
            status=payload.status,
            seating_type=payload.seating_type,
            ticket_type=payload.ticket_type,
        )
        self.repo.create(event)
        self._replace_categories(event, payload)
        self._replace_zones(event, payload.zones)
        self.db.commit()
        self.db.refresh(event)
        return self.repo.get_by_id(event.id)

    def update(self, event_id: str, payload: EventCreateRequest, host_id=None) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        if host_id is not None and str(event.host_id) != str(host_id):
            raise PermissionError("forbidden")
        if self.repo.has_sold_seats(event_id):
            raise ConflictError("cannot update event zones with sold seats")
        event.title = payload.title
        event.slug = slugify(payload.title)
        event.description = payload.description
        event.short_description = payload.short_description
        event.embedding = generate_embedding(self._build_embedding_text(payload.title, payload.description))
        event.start_time = payload.start_time
        event.end_time = payload.end_time
        event.venue = payload.venue
        event.banner_url = payload.banner_url
        event.is_private = payload.is_private
        event.theme = payload.theme
        event.status = payload.status
        event.seating_type = payload.seating_type
        event.ticket_type = payload.ticket_type
        event.max_capacity = payload.max_capacity
        self._replace_categories(event, payload)
        self._replace_zones(event, payload.zones)
        self.db.commit()
        return self.repo.get_by_id(event_id)

    def delete(self, event_id: str, host_id=None) -> None:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        if host_id is not None and str(event.host_id) != str(host_id):
            raise PermissionError("forbidden")
        if self.repo.has_sold_seats(event_id):
            raise ConflictError("cannot delete event with sold seats")
        self.db.delete(event)
        self.db.commit()

    def serialize(self, event: Event) -> EventResponse:
        return EventResponse(
            id=event.id,
            title=event.title,
            slug=event.slug,
            description=event.description,
            short_description=event.short_description,
            start_time=event.start_time,
            end_time=event.end_time,
            venue=event.venue,
            banner_url=event.banner_url,
            is_private=event.is_private,
            theme=event.theme,
            status=event.status,
            categories=[CategoryResponse.model_validate(item) for item in event.categories],
            zones=[SeatService.serialize_zone(zone) for zone in event.zones],
            seating_type=event.seating_type,
            ticket_type=event.ticket_type,
            max_capacity=event.max_capacity
        )

    def _replace_categories(self, event: Event, payload: EventCreateRequest) -> None:
        """
        Preferred: payload.categories contains full category objects copied from the response.
        Legacy fallback: payload.category_ids links to pre-created categories.
        """
        categories: list[Category] = []

        if payload.categories:
            category_ids = [category.id for category in payload.categories]
            category_map = {
                category.id: category
                for category in self.db.query(Category).filter(Category.id.in_(category_ids)).all()
            }
            if len(category_map) != len(set(category_ids)):
                raise ValueError("one or more categories do not exist")
            categories = [category_map[category_id] for category_id in category_ids]
        elif payload.category_ids:
            categories = list(
                self.db.query(Category).filter(Category.id.in_(payload.category_ids)).all()
            )
            if len(categories) != len(set(payload.category_ids)):
                raise ValueError("one or more categories do not exist")

        event.categories = categories
        self.db.flush()

    def _replace_zones(self, event: Event, zones) -> None:
        event.zones.clear()
        self.db.flush()
        for zone_payload in zones:
            zone = SeatZone(
                name=zone_payload.name,
                rows=zone_payload.rows,
                cols=zone_payload.cols,
                price=zone_payload.price,
                capacity=zone_payload.capacity or (zone_payload.rows * zone_payload.cols),
                color=zone_payload.color,
            )
            for row in range(1, zone_payload.rows + 1):
                for col in range(1, zone_payload.cols + 1):
                    label = f"{zone_payload.name.upper().replace(' ', '_')}-{chr(64 + row)}{col:02d}"
                    zone.seats.append(Seat(label=label, row_index=row - 1, col_index=col - 1))
            event.zones.append(zone)
        self.db.flush()
