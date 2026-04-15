from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.ticket import Ticket
from app.models.user import User


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def revenue_for_event(self, event_id: str) -> float:
        stmt = select(func.coalesce(func.sum(OrderItem.unit_price), 0)).where(OrderItem.event_id == event_id)
        return float(self.db.scalar(stmt) or 0)

    def gender_distribution(self, event_id: str) -> dict[str, int]:
        stmt = (
            select(User.gender, func.count(User.id))
            .join(Ticket, Ticket.user_id == User.id)
            .where(Ticket.event_id == event_id)
            .group_by(User.gender)
        )
        return {str(gender): count for gender, count in self.db.execute(stmt).all()}

    def age_distribution(self, event_id: str) -> dict[str, int]:
        today = date.today()
        age_years = func.date_part("year", func.age(today, User.date_of_birth))
        bracket = case(
            (age_years < 18, "<18"),
            (age_years.between(18, 25), "18-25"),
            (age_years.between(26, 35), "26-35"),
            (age_years.between(36, 50), "36-50"),
            else_="50+",
        )
        stmt = (
            select(bracket, func.count(User.id))
            .join(Ticket, Ticket.user_id == User.id)
            .where(Ticket.event_id == event_id)
            .group_by(bracket)
        )
        return {label: count for label, count in self.db.execute(stmt).all()}
