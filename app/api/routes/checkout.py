import base64

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession
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


@router.post("/checkout")
async def checkout(payload: CheckoutRequest, db: DbSession, user: CurrentUser):
    try:
        order, tickets = await CheckoutService(db).checkout(payload.seat_ids, user.id)
        return success_response(CheckoutResponse(
            order_id=order.id,
            total_amount=float(order.total_amount),
            tickets=[
                TicketItemResponse(
                    ticket_id=ticket.id,
                    event_id=ticket.event_id,
                    seat_id=ticket.seat_id,
                    qr_code=ticket.qr_code,
                    status=ticket.status,
                    purchased_at=ticket.purchased_at,
                )
                for ticket in tickets
            ],
        ))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/my-tickets")
def my_tickets(db: DbSession, user: CurrentUser):
    tickets = CheckoutService(db).list_my_tickets(user.id)
    return success_response([
        TicketDetailResponse(
            ticket_id=ticket.id,
            qr_code=ticket.qr_code,
            status=ticket.status,
            purchased_at=ticket.purchased_at,
            seat=TicketSeatResponse(
                id=ticket.seat.id,
                label=ticket.seat.label,
                row_index=ticket.seat.row_index,
                col_index=ticket.seat.col_index,
                status=ticket.seat.status.value,
            ),
            zone=TicketZoneResponse(
                id=ticket.seat.zone.id,
                name=ticket.seat.zone.name,
                color=ticket.seat.zone.color,
                price=float(ticket.seat.zone.price),
            ),
            event=TicketEventResponse(
                id=ticket.seat.zone.event.id,
                title=ticket.seat.zone.event.title,
                slug=ticket.seat.zone.event.slug,
                venue=ticket.seat.zone.event.venue,
                start_time=ticket.seat.zone.event.start_time,
                end_time=ticket.seat.zone.event.end_time,
                banner_url=ticket.seat.zone.event.banner_url,
            ),
        )
        for ticket in tickets
    ])


@router.get("/tickets/{ticket_id}")
def ticket_detail(ticket_id: str, db: DbSession, user: CurrentUser):
    try:
        ticket = CheckoutService(db).get_ticket(ticket_id, user.id)
        return success_response(
            TicketDetailResponse(
                ticket_id=ticket.id,
                qr_code=ticket.qr_code,
                status=ticket.status,
                purchased_at=ticket.purchased_at,
                seat=TicketSeatResponse(
                    id=ticket.seat.id,
                    label=ticket.seat.label,
                    row_index=ticket.seat.row_index,
                    col_index=ticket.seat.col_index,
                    status=ticket.seat.status.value,
                ),
                zone=TicketZoneResponse(
                    id=ticket.seat.zone.id,
                    name=ticket.seat.zone.name,
                    color=ticket.seat.zone.color,
                    price=float(ticket.seat.zone.price),
                ),
                event=TicketEventResponse(
                    id=ticket.seat.zone.event.id,
                    title=ticket.seat.zone.event.title,
                    slug=ticket.seat.zone.event.slug,
                    venue=ticket.seat.zone.event.venue,
                    start_time=ticket.seat.zone.event.start_time,
                    end_time=ticket.seat.zone.event.end_time,
                    banner_url=ticket.seat.zone.event.banner_url,
                ),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/tickets/{ticket_id}/qr")
def ticket_qr(ticket_id: str, db: DbSession, user: CurrentUser):
    try:
        ticket = CheckoutService(db).get_ticket(ticket_id, user.id)
        return Response(content=base64.b64decode(ticket.qr_code), media_type="image/png")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
