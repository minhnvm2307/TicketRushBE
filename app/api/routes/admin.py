from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.core.exceptions import ConflictError
from app.core.responses import success_response
# from app.schemas.dashboard import DashboardResponse, DemographicsResponse
from app.schemas.event import EventCreateRequest, EventUpdateRequest, SeatZonePayload
from app.services.dashboard import DashboardService
from app.services.events import EventService
from app.services.seats import SeatService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/events")
def list_events(db: DbSession, user: AdminUser):
    service = EventService(db)
    events = [service.serialize(event) for event in service.list_managed_by_host(user.id)]
    return success_response(events)

@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreateRequest, db: DbSession, user: AdminUser):
    event = EventService(db).create(payload, host_id=user.id)
    return success_response(EventService(db).serialize(event), status_code=status.HTTP_201_CREATED)


@router.get("/events/{event_id}")
def get_event(event_id: str, db: DbSession, user: AdminUser):
    event = EventService(db).repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")
    if str(event.host_id) != str(user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return success_response(EventService(db).serialize(event))


@router.put("/events/{event_id}")
def update_event(event_id: str, payload: EventUpdateRequest, db: DbSession, user: AdminUser):
    try:
        return success_response(EventService(db).serialize(EventService(db).update(event_id, payload, host_id=user.id)))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, db: DbSession, user: AdminUser):
    try:
        EventService(db).delete(event_id, host_id=user.id)
        return success_response({"deleted": True}, status_code=status.HTTP_200_OK)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
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
