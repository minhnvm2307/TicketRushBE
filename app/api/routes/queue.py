from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.services.queue import QueueService

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/status")
def queue_status(
    event_id: str,
    db: DbSession,
    user: CurrentUser,
    active_visitors: int = Query(default=0, ge=0),
):
    return success_response(QueueService(db).join_or_status(event_id, user.id, active_visitors))
