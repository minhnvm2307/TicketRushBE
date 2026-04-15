from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.core.responses import success_response
from app.schemas.dashboard import DashboardResponse, DemographicsResponse
from app.schemas.event import EventCreateRequest, SeatZonePayload
from app.services.dashboard import DashboardService
from app.services.events import EventService
from app.services.seats import SeatService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreateRequest, db: DbSession, _: AdminUser):
    return success_response(EventService(db).serialize(EventService(db).create(payload)), status_code=status.HTTP_201_CREATED)


@router.put("/events/{event_id}")
def update_event(event_id: str, payload: EventCreateRequest, db: DbSession, _: AdminUser):
    try:
        return success_response(EventService(db).serialize(EventService(db).update(event_id, payload)))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: DbSession, _: AdminUser):
    try:
        EventService(db).delete(event_id)
        return success_response({"deleted": True}, status_code=status.HTTP_200_OK)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/dashboard/{event_id}")
def dashboard(event_id: str, db: DbSession, _: AdminUser):
    return success_response(DashboardService(db).dashboard(event_id))


@router.get("/demographics/{event_id}")
def demographics(event_id: str, db: DbSession, _: AdminUser):
    return success_response(DashboardService(db).demographics(event_id))


@router.get("/events/{event_id}/zones")
def list_event_zones(event_id: str, db: DbSession, _: AdminUser):
    return success_response(SeatService(db).list_zones(event_id))


@router.post("/events/{event_id}/zones", status_code=status.HTTP_201_CREATED)
def create_event_zone(event_id: str, payload: SeatZonePayload, db: DbSession, _: AdminUser):
    return success_response(SeatService(db).create_zone(event_id, payload), status_code=status.HTTP_201_CREATED)
