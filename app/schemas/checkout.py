from datetime import datetime

from pydantic import BaseModel

from app.models.enums import TicketStatus
from app.schemas.common import APIModel


class CheckoutRequest(BaseModel):
    seat_ids: list[str]
    event_id: str


class TicketItemResponse(APIModel):
    ticket_id: str
    event_id: str
    seat_id: str
    qr_code: str
    status: TicketStatus
    purchased_at: datetime


class TicketEventResponse(APIModel):
    id: str
    title: str
    slug: str
    venue: str
    start_time: datetime
    end_time: datetime
    banner_url: str | None


class TicketZoneResponse(APIModel):
    id: str
    name: str
    color: str
    price: float


class TicketSeatResponse(APIModel):
    id: str
    label: str
    row_index: int
    col_index: int
    status: str


class TicketDetailResponse(APIModel):
    ticket_id: str
    qr_code: str
    status: TicketStatus
    purchased_at: datetime
    seat: TicketSeatResponse
    zone: TicketZoneResponse
    event: TicketEventResponse


class CheckoutResponse(APIModel):
    order_id: str
    total_amount: float
    tickets: list[TicketItemResponse]
