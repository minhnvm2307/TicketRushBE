from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import TicketStatus
from app.schemas.common import APIModel


class CheckoutRequest(BaseModel):
    event_id: UUID
    seat_ids: list[UUID] = Field(default_factory=list)
    quantity: int = 1

    @model_validator(mode="after")
    def validate_checkout_type(self) -> "CheckoutRequest":
        if self.quantity < 1:
            raise ValueError("quantity must be at least 1")
        return self


class TicketItemResponse(APIModel):
    ticket_id: UUID
    event_id: UUID
    zone_id: UUID
    seat_id: UUID | None
    qr_code: str
    status: TicketStatus
    purchased_at: datetime


class TicketEventResponse(APIModel):
    id: UUID
    title: str
    slug: str
    venue: str
    start_time: datetime
    end_time: datetime
    banner_url: str | None


class TicketZoneResponse(APIModel):
    id: UUID
    name: str
    color: str
    price: float


class TicketSeatResponse(APIModel):
    id: UUID
    label: str
    row_index: int
    col_index: int
    status: str


class TicketDetailResponse(APIModel):
    ticket_id: UUID
    qr_code: str
    status: TicketStatus
    purchased_at: datetime
    seat: TicketSeatResponse | None
    zone: TicketZoneResponse
    event: TicketEventResponse


class CheckoutResponse(APIModel):
    order_id: UUID
    total_amount: float
    tickets: list[TicketItemResponse]
