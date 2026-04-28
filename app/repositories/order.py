from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order
from app.models.seat import Seat, SeatZone
from app.models.ticket import Ticket


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.flush()
        return order

    def list_tickets_by_user(self, user_id: str) -> list[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .options(
                joinedload(Ticket.seat).joinedload(Seat.zone).joinedload(SeatZone.event),
                joinedload(Ticket.zone).joinedload(SeatZone.event),
            )
            .order_by(Ticket.purchased_at.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_ticket_by_id(self, ticket_id: str) -> Ticket | None:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(
                joinedload(Ticket.seat).joinedload(Seat.zone).joinedload(SeatZone.event),
                joinedload(Ticket.zone).joinedload(SeatZone.event),
            )
        )
        return self.db.scalar(stmt)
