from sqlalchemy.orm import Session

from app.models.enums import SeatStatus
from app.repositories.analytics import AnalyticsRepository
from app.repositories.event import EventRepository
from app.repositories.order import OrderRepository
from app.repositories.seat import SeatRepository
from app.services.realtime import connection_manager


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.analytics = AnalyticsRepository(db)
        self.events = EventRepository(db)
        self.orders = OrderRepository(db)
        self.seats = SeatRepository(db)

    def dashboard(self, event_id: str) -> dict:
        counts = self.seats.count_statuses_by_event(event_id)
        sold_count = max(
            self.orders.count_tickets_by_event(event_id),
            counts.get(SeatStatus.SOLD.value, 0),
        )
        locked_count = counts.get(SeatStatus.LOCKED.value, 0)
        capacity = self._capacity_for_event(event_id)
        available_count = max(capacity - sold_count - locked_count, 0)
        return {
            "event_id": event_id,
            "sold_count": sold_count,
            "locked_count": locked_count,
            "available_count": available_count,
            "revenue": self.analytics.revenue_for_event(event_id),
        }

    def _capacity_for_event(self, event_id: str) -> int:
        seat_count = self.seats.count_seats_by_event(event_id)
        if seat_count > 0:
            return seat_count

        event = self.events.get_by_id(event_id)
        return max(
            self.seats.capacity_by_event(event_id),
            int(event.max_capacity or 0) if event else 0,
        )

    async def broadcast_dashboard_update(self, event_id: str) -> None:
        payload = self.dashboard(event_id)
        payload["type"] = "dashboard_update"
        await connection_manager.broadcast(f"admin-dashboard:{event_id}", payload)

    def demographics(self, event_id: str) -> dict:
        return {
            "event_id": event_id,
            "age_distribution": self.analytics.age_distribution(event_id),
            "gender_distribution": self.analytics.gender_distribution(event_id),
        }
