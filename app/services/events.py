from re import sub

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ExpiredEventError
from app.models.enums import SeatingType, TicketType, ZoneType
from app.models.event import Category, Event
from app.models.seat import Seat, SeatZone
from app.repositories.event import EventRepository
from app.schemas.event import CategoryResponse, EventCreateRequest, EventResponse, EventUpdateRequest
from app.services.seats import SeatService
from app.services.embedding import generate_embedding_or_zero



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
            event.embedding = generate_embedding_or_zero(self._build_embedding_text(event.title, event.description))

        self.db.commit()
        return len(events)

    @staticmethod
    def _build_embedding_text(title: str, description: str) -> str:
        # Canonical semantic text for event vectors.
        return f"{title.strip()} {description.strip()}".strip()

    def get_public_detail(self, event_id: str) -> Event:
        event = self.repo.get_public_active_by_id(event_id)
        if not event:
            raise ExpiredEventError("event has ended or is unavailable")
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
            embedding=generate_embedding_or_zero(self._build_embedding_text(payload.title, payload.description)),
            start_time=payload.start_time,
            end_time=payload.end_time,
            venue=payload.venue,
            banner_url=payload.banner_url,
            is_private=payload.is_private,
            theme=payload.theme,
            status=payload.status,
            seating_type=payload.seating_type,
            ticket_type=payload.ticket_type,
            max_capacity=payload.max_capacity,
            seat_map_rows=payload.seat_map_rows,
            seat_map_cols=payload.seat_map_cols,
        )
        self.repo.create(event)
        self._replace_categories(event, payload)
        self._validate_zone_prices(payload.ticket_type, payload.zones)
        self._validate_layout_payload(
            payload.seating_type,
            payload.seat_map_rows,
            payload.seat_map_cols,
            payload.zones,
        )
        self._replace_zones(event, payload.zones)
        self.db.commit()
        self.db.refresh(event)
        return self.repo.get_by_id(event.id)

    def update(self, event_id: str, payload: EventUpdateRequest, host_id=None) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            raise ValueError("event not found")
        if host_id is not None and str(event.host_id) != str(host_id):
            raise PermissionError("forbidden")
        if payload.zones is not None and self.repo.has_sold_seats(event_id):
            raise ConflictError("cannot update event zones with sold seats")
        next_title = payload.title if payload.title is not None else event.title
        next_description = payload.description if payload.description is not None else event.description

        event.title = next_title
        event.slug = slugify(next_title)
        event.description = next_description
        if payload.short_description is not None:
            event.short_description = payload.short_description
        event.embedding = generate_embedding_or_zero(self._build_embedding_text(next_title, next_description))
        if payload.start_time is not None:
            event.start_time = payload.start_time
        if payload.end_time is not None:
            event.end_time = payload.end_time
        if payload.venue is not None:
            event.venue = payload.venue
        if payload.banner_url is not None:
            event.banner_url = payload.banner_url
        if payload.is_private is not None:
            event.is_private = payload.is_private
        if payload.theme is not None:
            event.theme = payload.theme
        if payload.status is not None:
            event.status = payload.status
        if payload.seating_type is not None:
            event.seating_type = payload.seating_type
            if event.seating_type == SeatingType.GENERAL_ADMISSION:
                event.seat_map_rows = None
                event.seat_map_cols = None
        if payload.ticket_type is not None:
            event.ticket_type = payload.ticket_type
        if payload.max_capacity is not None:
            event.max_capacity = payload.max_capacity
        if payload.seat_map_rows is not None:
            event.seat_map_rows = payload.seat_map_rows
        if payload.seat_map_cols is not None:
            event.seat_map_cols = payload.seat_map_cols
        if payload.categories is not None or payload.category_ids is not None:
            self._replace_categories(event, payload)
        if payload.zones is not None:
            self._validate_zone_prices(event.ticket_type, payload.zones)
            self._validate_layout_payload(
                event.seating_type,
                event.seat_map_rows,
                event.seat_map_cols,
                payload.zones,
            )
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
            max_capacity=event.max_capacity,
            seat_map_rows=event.seat_map_rows,
            seat_map_cols=event.seat_map_cols,
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
            zone_type = (
                ZoneType.GENERAL_ADMISSION
                if event.seating_type == SeatingType.GENERAL_ADMISSION
                else zone_payload.zone_type
            )
            is_assigned_zone = zone_type == ZoneType.ASSIGNED
            zone = SeatZone(
                name=zone_payload.name,
                zone_type=zone_type,
                price=zone_payload.price or 0,
                capacity=len(zone_payload.seats) if is_assigned_zone else (zone_payload.capacity or event.max_capacity or 1),
                color=zone_payload.color,
            )
            if is_assigned_zone:
                for seat_payload in zone_payload.seats:
                    zone.seats.append(
                        Seat(
                            event_id=event.id,
                            label=seat_payload.label.strip(),
                            row_index=seat_payload.row_index,
                            col_index=seat_payload.col_index,
                            display_order=seat_payload.display_order,
                        )
                    )
            event.zones.append(zone)
        self.db.flush()

    def _validate_layout_payload(self, seating_type, seat_map_rows, seat_map_cols, zones) -> None:
        if seating_type != SeatingType.ASSIGNED:
            return
        if seat_map_rows is None or seat_map_cols is None:
            raise ValueError("seat_map_rows and seat_map_cols are required for assigned seating")
        if not zones:
            raise ValueError("assigned seating events require at least one zone")

        seen_positions: set[tuple[int, int]] = set()
        seen_labels: set[str] = set()
        has_assigned_seat = False
        for zone in zones:
            if zone.zone_type != ZoneType.ASSIGNED:
                continue
            if not zone.seats:
                raise ValueError("each assigned zone must have at least one seat")
            for seat in zone.seats:
                has_assigned_seat = True
                if seat.row_index >= seat_map_rows or seat.col_index >= seat_map_cols:
                    raise ValueError("seat coordinates must be inside the seat map bounds")
                position = (seat.row_index, seat.col_index)
                if position in seen_positions:
                    raise ValueError("duplicate seat position in event")
                seen_positions.add(position)
                label = seat.label.strip()
                if label in seen_labels:
                    raise ValueError("duplicate seat label in event")
                seen_labels.add(label)
        if not has_assigned_seat:
            raise ValueError("assigned seating events require at least one seat")

    def _validate_zone_prices(self, ticket_type, zones) -> None:
        for zone in zones:
            price = zone.price or 0
            if ticket_type == TicketType.FREE and price != 0:
                raise ValueError("All zones must have a price of 0 for FREE ticket type")
            if ticket_type == TicketType.PAID and price <= 0:
                raise ValueError("All zones must have a positive price for PAID ticket type")
