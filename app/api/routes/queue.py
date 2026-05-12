from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.repositories.event import EventRepository
from app.services.queue import QueueService

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("/status/{event_id}")
def get_queue_status(event_id: str, db: DbSession, user: CurrentUser) -> dict:
    """
    Get the current user's status in the queue for an event.
    """
    if not EventRepository(db).get_public_active_by_id(event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event has ended or is unavailable")
    status_data = QueueService().get_queue_status(event_id, user.id)
    return success_response(status_data)


@router.post("/join/{event_id}")
def join_queue(event_id: str, db: DbSession, user: CurrentUser) -> dict:
    """
    Join the queue for an event.
    """
    if not EventRepository(db).get_public_active_by_id(event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event has ended or is unavailable")
    status_data = QueueService().join_queue(event_id, user.id)
    return success_response(status_data)
