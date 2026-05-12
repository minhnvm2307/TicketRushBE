import base64

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import ExpiredEventError
from app.core.responses import success_response
from app.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
    TicketDetailResponse,
    TicketEventResponse,
    TicketItemResponse,
    TicketSeatResponse,
    TicketZoneResponse,
)
from app.services.checkout import CheckoutService

router = APIRouter(tags=["checkout"])


def build_ticket_detail_response(ticket) -> TicketDetailResponse:
    zone = ticket.zone or (ticket.seat.zone if ticket.seat else None)
    event = zone.event if zone else None
    if zone is None or event is None:
        raise ValueError("ticket is missing zone or event data")

    seat_response = None
    if ticket.seat:
        seat_response = TicketSeatResponse(
            id=ticket.seat.id,
            label=ticket.seat.label,
            row_index=ticket.seat.row_index,
            col_index=ticket.seat.col_index,
            status=ticket.seat.status.value,
        )

    return TicketDetailResponse(
        ticket_id=ticket.id,
        qr_code=ticket.qr_code,
        status=ticket.status,
        purchased_at=ticket.purchased_at,
        seat=seat_response,
        zone=TicketZoneResponse(
            id=zone.id,
            name=zone.name,
            color=zone.color,
            price=float(zone.price),
        ),
        event=TicketEventResponse(
            id=event.id,
            title=event.title,
            slug=event.slug,
            venue=event.venue,
            start_time=event.start_time,
            end_time=event.end_time,
            banner_url=event.banner_url,
        ),
    )


@router.post("/checkout")
async def checkout(payload: CheckoutRequest, db: DbSession, user: CurrentUser):
    try:
        order, tickets = await CheckoutService(db).checkout(
            [str(seat_id) for seat_id in payload.seat_ids],
            str(user.id),
            str(payload.event_id),
            payload.quantity,
        )
        return success_response(CheckoutResponse(
            order_id=order.id,
            total_amount=float(order.total_amount),
            tickets=[
                TicketItemResponse(
                    ticket_id=ticket.id,
                    event_id=ticket.event_id,
                    zone_id=ticket.zone_id,
                    seat_id=ticket.seat_id,
                    qr_code=ticket.qr_code,
                    status=ticket.status,
                    purchased_at=ticket.purchased_at,
                )
                for ticket in tickets
            ],
        ))
    except ExpiredEventError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/my-tickets")
def my_tickets(db: DbSession, user: CurrentUser):
    tickets = CheckoutService(db).list_my_tickets(str(user.id))
    return success_response([build_ticket_detail_response(ticket) for ticket in tickets])


@router.get("/tickets/{ticket_id}")
def ticket_detail(ticket_id: str, db: DbSession, user: CurrentUser):
    try:
        ticket = CheckoutService(db).get_ticket(ticket_id, str(user.id))
        return success_response(build_ticket_detail_response(ticket))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}/qr")
def ticket_qr(ticket_id: str, db: DbSession, user: CurrentUser):
    try:
        ticket = CheckoutService(db).get_ticket(ticket_id, str(user.id))
        return Response(content=base64.b64decode(ticket.qr_code), media_type="image/png")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
