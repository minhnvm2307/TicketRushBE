from datetime import datetime

from pydantic import BaseModel

from app.models.enums import SeatStatus
from app.schemas.common import APIModel


class SeatHoldRequest(BaseModel):
    seat_id: str


class SeatHoldResponse(BaseModel):
    seat_id: str
    locked_until: datetime
    message: str


class SeatMapSeatResponse(APIModel):
    id: str
    label: str
    row_index: int
    col_index: int
    status: SeatStatus
    locked_by: str | None = None
    locked_until: datetime | None = None


class SeatMapZoneResponse(APIModel):
    id: str
    name: str
    rows: int
    cols: int
    capacity: int
    price: float
    color: str
    seats: list[SeatMapSeatResponse]


class SeatMapResponse(APIModel):
    event_id: str
    zones: list[SeatMapZoneResponse]
