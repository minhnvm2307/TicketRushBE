from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EventStatus, SeatStatus, SeatingType, TicketType
from app.schemas.common import APIModel


class SeatZonePayload(BaseModel):
    name: str
    rows: int = Field(ge=1)
    cols: int = Field(ge=1)
    price: float | None = None
    color: str
    capacity: int | None = Field(default=None, ge=0)


class CategoryPayload(APIModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class EventCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str
    short_description: str = Field(default="", max_length=500)
    start_time: datetime | None = None
    end_time: datetime | None = None
    event_date: datetime | None = None
    venue: str
    banner_url: str | None = None
    is_private: bool = False
    theme: str = Field(default="minimal", max_length=50)
    status: EventStatus = EventStatus.DRAFT
    # Preferred: full category objects copied from `CategoryResponse`
    categories: list[CategoryPayload] = Field(default_factory=list)
    # Legacy fallback for older clients that still send ids only
    category_ids: list[UUID] = Field(default_factory=list)
    seating_type: SeatingType = SeatingType.ASSIGNED
    ticket_type: TicketType = TicketType.PAID
    zones: list[SeatZonePayload] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_time_fields(cls, values: dict):
        if not isinstance(values, dict):
            return values
        legacy_event_date = values.get("event_date")
        if legacy_event_date and not values.get("start_time"):
            values["start_time"] = legacy_event_date
        return values
    
    @model_validator(mode="before")
    @classmethod
    def ticket_type_price(cls, values: dict):
        if not isinstance(values, dict):
            return values
        
        ticket_type = values.get("ticket_type")
        zones = values.get("zones", [])
        
        if ticket_type == TicketType.PAID:
            for zone in zones:
                price = zone.get("price")
                if price is None or price <= 0:
                    raise ValueError("All zones must have a positive price for PAID ticket type")
                    
        if ticket_type == TicketType.FREE:
            for zone in zones:
                price = zone.get("price")
                if price is not None and price != 0:
                    raise ValueError("All zones must have a price of 0 for FREE ticket type")
        return values

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time is not None and self.end_time is None:
            self.end_time = self.start_time + timedelta(hours=2)
        if self.start_time is None or self.end_time is None:
            raise ValueError("start_time and end_time are required")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class EventUpdateRequest(EventCreateRequest):
    pass


class SeatResponse(APIModel):
    id: UUID
    label: str
    row_index: int
    col_index: int
    status: SeatStatus
    locked_by: str | None = None
    locked_until: datetime | None = None


class ZoneResponse(APIModel):
    id: UUID
    name: str
    # Some zones (e.g., non-assigned/standing) may not have a row/col grid.
    rows: int | None = None
    cols: int | None = None
    price: float
    capacity: int
    color: str
    seats: list[SeatResponse]


class CategoryResponse(CategoryPayload):
    pass


class EventResponse(APIModel):
    id: UUID
    title: str
    slug: str
    description: str
    short_description: str
    start_time: datetime
    end_time: datetime
    venue: str
    banner_url: str | None
    is_private: bool
    theme: str
    status: EventStatus
    categories: list[CategoryResponse]
    zones: list[ZoneResponse]
    seating_type: SeatingType
    ticket_type: TicketType
    max_capacity: int | None = None


class EventListItem(APIModel):
    id: UUID
    title: str
    slug: str
    start_time: datetime
    end_time: datetime
    venue: str
    banner_url: str | None
    lowest_price: float | None
    categories: list[CategoryResponse]
    seating_type: SeatingType
    ticket_type: TicketType
    max_capacity: int | None = None
    cosine_distance: float | None = None
    similarity_score: float | None = None
