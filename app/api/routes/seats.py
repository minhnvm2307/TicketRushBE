from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import ExpiredEventError
from app.core.responses import success_response
from app.schemas.seat import SeatHoldRequest, SeatHoldResponse
from app.services.seats import SeatService

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.post("/{seat_id}/hold", response_model=SeatHoldResponse)
async def hold_seat(seat_id: str, payload: SeatHoldRequest, db: DbSession, user: CurrentUser):
    try:
        session_id = getattr(user, "_token_payload", {}).get("sid")
        result = await SeatService(db).hold(seat_id, str(user.id), payload.event_id, session_id=session_id)
        return success_response(result)
    except ExpiredEventError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.delete("/{seat_id}/hold")
async def release_seat(seat_id: str, payload: SeatHoldRequest, db: DbSession, user: CurrentUser):
    try:
        await SeatService(db).release(seat_id, str(user.id), payload.event_id)
        return success_response({"message": "Seat released successfully"})
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
