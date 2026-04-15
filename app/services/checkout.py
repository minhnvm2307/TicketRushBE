import base64
from datetime import UTC, datetime
from io import BytesIO

import qrcode
from sqlalchemy.orm import Session

from app.core.redis import get_redis_client, redis_is_enabled
from app.models.enums import InteractionType, OrderStatus, SeatStatus, TicketStatus
from app.models.interaction import UserEventInteraction
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket
from app.repositories.interaction import InteractionRepository
from app.repositories.order import OrderRepository
from app.repositories.seat import SeatRepository
from app.services.dashboard import DashboardService
from app.services.realtime import connection_manager


class CheckoutService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.seats = SeatRepository(db)
        self.interactions = InteractionRepository(db)
        self.redis = get_redis_client() if redis_is_enabled() else None

    async def checkout(self, seat_ids: list[str], user_id: str) -> tuple[Order, list[Ticket]]:
        seats = self.seats.get_many_for_update(seat_ids)
        if len(seats) != len(seat_ids):
            raise ValueError("one or more seats do not exist")

        total = 0.0
        order = Order(user_id=user_id, status=OrderStatus.PAID, paid_at=datetime.now(UTC))
        self.orders.create(order)
        tickets: list[Ticket] = []

        for seat in seats:
            if seat.locked_by != user_id or seat.status != SeatStatus.LOCKED:
                raise ValueError("seat hold is invalid or expired")
            seat.status = SeatStatus.SOLD
            total += float(seat.zone.price)
            order.items.append(
                OrderItem(
                    event_id=seat.zone.event_id,
                    seat_id=seat.id,
                    zone_name=seat.zone.name,
                    seat_label=seat.label,
                    unit_price=seat.zone.price,
                )
            )
            ticket = Ticket(
                order_id=order.id,
                event_id=seat.zone.event_id,
                seat_id=seat.id,
                user_id=user_id,
                qr_code=self._generate_qr_payload(order.id, seat.id),
                status=TicketStatus.VALID,
            )
            tickets.append(ticket)
            self.db.add(ticket)
            self.interactions.add(
                UserEventInteraction(
                    user_id=user_id, event_id=seat.zone.event_id, interaction_type=InteractionType.PURCHASE
                )
            )

        order.total_amount = total
        self.db.commit()
        if self.redis:
            for seat in seats:
                self.redis.delete(f"seat_hold:{seat.id}")

        for seat in seats:
            await connection_manager.broadcast(
                seat.zone.event_id,
                {
                    "type": "seat_status_changed",
                    "seat_id": seat.id,
                    "status": SeatStatus.SOLD.value,
                    "locked_by": None,
                },
            )
            await DashboardService(self.db).broadcast_dashboard_update(seat.zone.event_id)
        return order, tickets

    def list_my_tickets(self, user_id: str) -> list[Ticket]:
        return self.orders.list_tickets_by_user(user_id)

    def get_ticket(self, ticket_id: str, user_id: str) -> Ticket:
        ticket = self.orders.get_ticket_by_id(ticket_id)
        if not ticket or ticket.user_id != user_id:
            raise ValueError("ticket not found")
        return ticket

    def _generate_qr_payload(self, order_id: str, seat_id: str) -> str:
        image = qrcode.make(f"order:{order_id}|seat:{seat_id}")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
