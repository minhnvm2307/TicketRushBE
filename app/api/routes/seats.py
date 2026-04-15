from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
# from app.schemas.event import SeatZonePayload
from app.schemas.seat import SeatHoldRequest, SeatHoldResponse
from app.services.seats import SeatService

router = APIRouter(prefix="/seats", tags=["seats"])


@router.post("/hold")
async def hold_seat(payload: SeatHoldRequest, db: DbSession, user: CurrentUser):
    try:
        locked_until = await SeatService(db).hold(payload.seat_id, user.id)
        return success_response(SeatHoldResponse(seat_id=payload.seat_id, locked_until=locked_until, message="seat locked"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{seat_id}/hold")
async def release_seat(seat_id: str, db: DbSession, user: CurrentUser):
    try:
        await SeatService(db).release(seat_id, user.id)
        return success_response({"message": "seat released"})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

