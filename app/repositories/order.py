from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import TicketStatus
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

    def count_tickets_by_user_event(self, user_id: str, event_id: str) -> int:
        stmt = select(func.count(Ticket.id)).where(
            Ticket.user_id == user_id,
            Ticket.event_id == event_id,
            Ticket.status != TicketStatus.REFUNDED,
        )
        return int(self.db.scalar(stmt) or 0)

    def count_tickets_by_event(self, event_id: str) -> int:
        stmt = select(func.count(Ticket.id)).where(
            Ticket.event_id == event_id,
            Ticket.status != TicketStatus.REFUNDED,
        )
        return int(self.db.scalar(stmt) or 0)
