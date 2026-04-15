from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import SeatStatus
from app.schemas.common import APIModel


class SeatHoldRequest(BaseModel):
    event_id: UUID = Field(..., description="The ID of the event to which the seat belongs.")


class SeatHoldResponse(BaseModel):
    seat_id: str
    status: str
    locked_until: datetime


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
