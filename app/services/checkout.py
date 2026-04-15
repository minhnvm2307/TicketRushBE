import base64
from datetime import UTC, datetime
from io import BytesIO

import qrcode
from sqlalchemy.orm import Session

from app.core.redis import RedisKey, get_redis_client, loads_payload, redis_is_enabled
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

    async def checkout(self, seat_ids: list[str], user_id: str, event_id: str) -> tuple[Order, list[Ticket]]:
        if not self.redis:
            raise ConnectionError("Redis is not enabled or connected")

        # Step 1: Validate Redis locks
        lock_keys = [RedisKey.seat_lock(event_id, seat_id) for seat_id in seat_ids]
        lock_data_raw = self.redis.mget(lock_keys)

        for i, lock_raw in enumerate(lock_data_raw):
            if not lock_raw:
                raise ValueError(f"Lock for seat {seat_ids[i]} has expired or does not exist.")
            lock_data = loads_payload(lock_raw)
            if lock_data.get("user_id") != user_id:
                raise ValueError(f"Seat {seat_ids[i]} is held by another user.")

        # Step 2: Process the order in a transaction
        try:
            with self.db.begin_nested():
                seats = self.seats.get_many_by_ids(seat_ids)
                if len(seats) != len(seat_ids):
                    raise ValueError("One or more seats do not exist.")

                for seat in seats:
                    if seat.status == SeatStatus.SOLD:
                        raise ValueError(f"Seat {seat.id} is already sold.")

                total = sum(seat.zone.price for seat in seats)
                order = Order(user_id=user_id, status=OrderStatus.PAID, paid_at=datetime.now(UTC), total_amount=total)
                self.orders.create(order)
                tickets: list[Ticket] = []

                for seat in seats:
                    seat.status = SeatStatus.SOLD
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
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        # Step 3: Delete Redis locks after successful DB commit
        self.redis.delete(*lock_keys)

        # Step 4: Broadcast updates
        for seat in seats:
            await connection_manager.broadcast(
                seat.zone.event_id,
                {
                    "type": "seat_status_changed",
                    "seat_id": seat.id,
                    "status": "SOLD",
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
