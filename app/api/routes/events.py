from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.core.responses import success_response
from app.services.events import EventService
from app.services.seats import SeatService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(
    db: DbSession,
    search: str | None = Query(default=None, description="Search by event title"),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
):
    return success_response(EventService(db).list_public(search, date_from, date_to))


@router.get("/{event_id}")
def get_event(event_id: str, db: DbSession):
    try:
        event = EventService(db).get_public_detail(event_id)
        return success_response(EventService(db).serialize(event))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{event_id}/seats")
def get_event_seats(event_id: str, db: DbSession):
    return success_response(SeatService(db).get_seat_map(event_id))
