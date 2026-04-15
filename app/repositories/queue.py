from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.queue import QueueEntry


class QueueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_for_event(self, event_id: str) -> int:
        stmt = select(QueueEntry).where(QueueEntry.event_id == event_id)
        return len(list(self.db.scalars(stmt).all()))

    def find_by_user(self, event_id: str, user_id: str) -> QueueEntry | None:
        stmt = select(QueueEntry).where(QueueEntry.event_id == event_id, QueueEntry.user_id == user_id)
        return self.db.scalar(stmt)

    def add(self, entry: QueueEntry) -> QueueEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def position(self, event_id: str, created_at: datetime) -> int:
        stmt = select(QueueEntry).where(QueueEntry.event_id == event_id, QueueEntry.created_at <= created_at)
        return len(list(self.db.scalars(stmt).all()))

    def list_waiting(self, event_id: str) -> list[QueueEntry]:
        stmt = (
            select(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .order_by(QueueEntry.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def cleanup_expired(self) -> None:
        now = datetime.now(UTC)
        self.db.query(QueueEntry).filter(QueueEntry.expires_at.is_not(None), QueueEntry.expires_at < now).delete()
