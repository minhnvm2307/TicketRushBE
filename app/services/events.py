from re import sub

from sqlalchemy.orm import Session

from app.models.event import Event, EventCategory, EventTag
from app.models.seat import Seat, SeatZone
from app.repositories.event import EventRepository
from app.schemas.event import EventCreateRequest, EventResponse


def slugify(value: str) -> str:
    value = sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "event"


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EventRepository(db)

    def list_public(self, search: str | None, date_from, date_to):
        events = self.repo.list_published(search, date_from, date_to)
        response = []
        for event in events:
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
                    "categories": [item.name for item in event.categories],
                    "tags": [item.name for item in event.tags],
                }
            )
        return response

    def get_public_detail(self, event_id: str) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        return event

    def create(self, payload: EventCreateRequest) -> Event:
        event = Event(
            title=payload.title,
            slug=slugify(payload.title),
            description=payload.description,
            short_description=payload.short_description,
            start_time=payload.start_time,
            end_time=payload.end_time,
            venue=payload.venue,
            banner_url=payload.banner_url,
            is_private=payload.is_private,
            theme=payload.theme,
            status=payload.status,
        )
        self.repo.create(event)
        self._replace_taxonomy(event, payload.categories, payload.tags)
        self._replace_zones(event, payload.zones)
        self.db.commit()
        self.db.refresh(event)
        return self.repo.get_by_id(event.id)

    def update(self, event_id: str, payload: EventCreateRequest) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        event.title = payload.title
        event.slug = slugify(payload.title)
        event.description = payload.description
        event.short_description = payload.short_description
        event.start_time = payload.start_time
        event.end_time = payload.end_time
        event.venue = payload.venue
        event.banner_url = payload.banner_url
        event.is_private = payload.is_private
        event.theme = payload.theme
        event.status = payload.status
        self._replace_taxonomy(event, payload.categories, payload.tags)
        self._replace_zones(event, payload.zones)
        self.db.commit()
        return self.repo.get_by_id(event_id)

    def delete(self, event_id: str) -> None:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        if self.repo.has_sold_seats(event_id):
            raise ValueError("cannot delete event with sold seats")
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
            categories=[item.name for item in event.categories],
            tags=[item.name for item in event.tags],
            zones=event.zones,
        )

    def _replace_taxonomy(self, event: Event, categories: list[str], tags: list[str]) -> None:
        event.categories = [EventCategory(name=name.strip().lower()) for name in categories if name.strip()]
        event.tags = [EventTag(name=name.strip().lower()) for name in tags if name.strip()]
        self.db.flush()

    def _replace_zones(self, event: Event, zones) -> None:
        event.zones = []
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
