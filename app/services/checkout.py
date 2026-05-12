import base64
from datetime import UTC, datetime
from io import BytesIO

import qrcode
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import RedisKey, get_redis_client, loads_payload, redis_is_enabled
from app.core.exceptions import ExpiredEventError
from app.models.enums import InteractionType, OrderStatus, SeatStatus, SeatingType, TicketStatus, TicketType, ZoneType
from app.models.interaction import UserEventInteraction
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket
from app.repositories.event import EventRepository
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
        self.events = EventRepository(db)
        self.interactions = InteractionRepository(db)
        self.settings = get_settings()
        self.redis = get_redis_client() if redis_is_enabled() else None

    def _max_bookable_for_event(self, event) -> int:
        return int(getattr(event, "max_bookable", None) or self.settings.default_max_bookable_per_user)

    def _has_admission_access(self, event_id: str, user_id: str) -> bool:
        if not self.redis:
            return False
        return self.redis.ttl(RedisKey.booking_session(str(event_id), str(user_id))) > 0

    def _enforce_max_bookable(self, event, user_id: str, requested_count: int) -> None:
        tickets_bought = self.orders.count_tickets_by_user_event(user_id, str(event.id))
        max_bookable = self._max_bookable_for_event(event)
        if tickets_bought + requested_count > max_bookable:
            raise ValueError(f"You can only purchase up to {max_bookable} tickets for this event.")

    def _enforce_free_ticket_limit(self, event, requested_count: int) -> None:
        if event.ticket_type != TicketType.FREE:
            return
        if requested_count != 1:
            raise ValueError("Free events allow exactly 1 ticket per checkout.")

    async def checkout(self, seat_ids: list[str], user_id: str, event_id: str, quantity: int = 1) -> tuple[Order, list[Ticket]]:
        if not self.redis:
            raise ConnectionError("Redis is not enabled or connected")
        event = self.events.get_public_active_by_id(event_id)
        if not event:
            raise ExpiredEventError("event has ended or is unavailable")
        if event.seating_type == SeatingType.GENERAL_ADMISSION:
            self._enforce_free_ticket_limit(event, quantity)
            return await self._checkout_general_admission(event, user_id, quantity)
        if not seat_ids:
            raise ValueError("seat_ids must not be empty for assigned seating events.")
        if event.seating_type == SeatingType.ASSIGNED and not self._has_admission_access(event.id, user_id):
            raise ValueError("Your queue access has expired. Please rejoin the queue.")
        self._enforce_free_ticket_limit(event, len(seat_ids))
        return await self._checkout_assigned(event, seat_ids, user_id)

    async def _checkout_assigned(self, event, seat_ids: list[str], user_id: str) -> tuple[Order, list[Ticket]]:
        self._enforce_max_bookable(event, user_id, len(seat_ids))

        now = datetime.now(UTC)
        event_id = str(event.id)
        lock_keys = [RedisKey.seat_lock(event_id, seat_id) for seat_id in seat_ids]
        lock_data_raw = self.redis.mget(lock_keys)

        for i, lock_raw in enumerate(lock_data_raw):
            if not lock_raw:
                raise ValueError(f"Lock for seat {seat_ids[i]} has expired or does not exist.")
            lock_data = loads_payload(lock_raw)
            if lock_data.get("user_id") != user_id:
                raise ValueError(f"Seat {seat_ids[i]} is held by another user.")

        try:
            with self.db.begin_nested():
                self.seats.release_expired_holds(now)
                seats = self.seats.get_many_by_ids_for_update(seat_ids)
                if len(seats) != len(seat_ids):
                    raise ValueError("One or more seats do not exist.")
                event_ids = {str(seat.zone.event_id) for seat in seats}
                if event_ids != {str(event_id)}:
                    raise ValueError("One or more seats do not belong to this event.")

                for seat in seats:
                    if seat.status == SeatStatus.SOLD:
                        raise ValueError(f"Seat {seat.id} is already sold.")
                    if seat.status != SeatStatus.LOCKED:
                        raise ValueError(f"Seat {seat.id} is not locked.")
                    if str(seat.locked_by) != str(user_id):
                        raise ValueError(f"Seat {seat.id} is held by another user.")
                    if seat.locked_until is None or seat.locked_until <= now:
                        raise ValueError(f"Lock for seat {seat.id} has expired.")

                total = sum(seat.zone.price for seat in seats)
                order = Order(
                    user_id=user_id,
                    event_id=event_id,
                    status=OrderStatus.PAID,
                    paid_at=now,
                    total_amount=total,
                )
                self.orders.create(order)
                tickets: list[Ticket] = []

                for seat in seats:
                    seat.status = SeatStatus.SOLD
                    seat.locked_by = None
                    seat.locked_until = None
                    order.items.append(
                        OrderItem(
                            event_id=seat.zone.event_id,
                            zone_id=seat.zone.id,
                            seat_id=seat.id,
                            zone_name=seat.zone.name,
                            seat_label=seat.label,
                            unit_price=seat.zone.price,
                        )
                    )
                    ticket = Ticket(
                        order_id=order.id,
                        event_id=seat.zone.event_id,
                        zone_id=seat.zone.id,
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
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("One or more seats were already purchased.") from exc
        except Exception:
            self.db.rollback()
            raise

        self.redis.delete(*lock_keys)
        hold_index_key = RedisKey.user_event_hold_index(str(user_id), str(event_id))
        if seat_ids:
            self.redis.zrem(hold_index_key, *[str(seat_id) for seat_id in seat_ids])
        if self.redis.zcard(hold_index_key) == 0:
            self.redis.delete(RedisKey.booking_session(str(event_id), str(user_id)))

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

    async def _checkout_general_admission(self, event, user_id: str, quantity: int) -> tuple[Order, list[Ticket]]:
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        if event.seating_type != SeatingType.GENERAL_ADMISSION:
            raise ValueError("General admission checkout is not supported for this event.")

        ga_zone = self.seats.get_general_admission_zone_for_event(str(event.id))
        if not ga_zone or ga_zone.zone_type != ZoneType.GENERAL_ADMISSION:
            raise ValueError("General admission zone not found for this event.")

        if event.max_capacity is not None:
            sold_count = self.orders.count_tickets_by_event(str(event.id))
            if sold_count + quantity > event.max_capacity:
                raise ValueError("Event capacity has been reached for the requested quantity.")

        self._enforce_max_bookable(event, user_id, quantity)

        now = datetime.now(UTC)
        total = float(ga_zone.price) * quantity
        order = Order(
            user_id=user_id,
            event_id=event.id,
            status=OrderStatus.PAID,
            paid_at=now,
            total_amount=total,
        )
        tickets: list[Ticket] = []

        try:
            with self.db.begin_nested():
                self.orders.create(order)
                for _ in range(quantity):
                    order.items.append(
                        OrderItem(
                            event_id=event.id,
                            zone_id=ga_zone.id,
                            seat_id=None,
                            zone_name=ga_zone.name,
                            seat_label=None,
                            unit_price=ga_zone.price,
                        )
                    )
                    ticket = Ticket(
                        order_id=order.id,
                        event_id=event.id,
                        zone_id=ga_zone.id,
                        seat_id=None,
                        user_id=user_id,
                        qr_code=self._generate_qr_payload(order.id, f"ga:{ga_zone.id}:{len(tickets)}"),
                        status=TicketStatus.VALID,
                    )
                    tickets.append(ticket)
                    self.db.add(ticket)
                    self.interactions.add(
                        UserEventInteraction(
                            user_id=user_id,
                            event_id=event.id,
                            interaction_type=InteractionType.PURCHASE,
                        )
                    )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Unable to complete general admission checkout.") from exc
        except Exception:
            self.db.rollback()
            raise

        await DashboardService(self.db).broadcast_dashboard_update(str(event.id))
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
