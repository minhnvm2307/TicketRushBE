from sqlalchemy.orm import Session

from app.repositories.analytics import AnalyticsRepository
from app.repositories.seat import SeatRepository
from app.services.realtime import connection_manager


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.analytics = AnalyticsRepository(db)
        self.seats = SeatRepository(db)

    def dashboard(self, event_id: str) -> dict:
        counts = self.seats.count_statuses_by_event(event_id)
        return {
            "event_id": event_id,
            "sold_count": counts.get("sold", 0),
            "locked_count": counts.get("locked", 0),
            "available_count": counts.get("available", 0),
            "revenue": self.analytics.revenue_for_event(event_id),
        }

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
