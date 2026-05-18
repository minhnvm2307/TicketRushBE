from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import SeatStatus
from app.schemas.common import APIModel


class SeatHoldRequest(BaseModel):
    event_id: UUID = Field(..., description="The ID of the event to which the seat belongs.")


class SeatHoldResponse(BaseModel):
    seat_id: UUID
    status: str
    locked_until: datetime


class SeatMapSeatResponse(APIModel):
    id: UUID
    label: str
    row_index: int
    col_index: int
    display_order: int = 0
    status: SeatStatus
    locked_by: UUID | None = None
    locked_until: datetime | None = None


class SeatMapZoneResponse(APIModel):
    id: UUID
    name: str
    zone_type: str
    rows: int | None = None
    cols: int | None = None
    capacity: int
    price: float
    color: str
    seats: list[SeatMapSeatResponse]


class SeatMapResponse(APIModel):
    event_id: UUID
    seat_map_rows: int | None = None
    seat_map_cols: int | None = None
    zones: list[SeatMapZoneResponse]
