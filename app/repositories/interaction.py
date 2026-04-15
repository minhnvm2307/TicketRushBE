from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interaction import UserEventInteraction


class InteractionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, interaction: UserEventInteraction) -> None:
        self.db.add(interaction)
        self.db.flush()

    def list_by_user(self, user_id: str) -> list[UserEventInteraction]:
        stmt = select(UserEventInteraction).where(UserEventInteraction.user_id == user_id)
        return list(self.db.scalars(stmt).all())
