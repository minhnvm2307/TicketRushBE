import asyncio
import logging
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.services.dashboard import DashboardService
from app.services.realtime import connection_manager
from app.repositories.seat import SeatRepository

logger = logging.getLogger(__name__)


async def release_expired_holds_job() -> None:
    while True:
        db = SessionLocal()
        try:
            expired_seats = SeatRepository(db).release_expired_holds(datetime.now(UTC))
            if expired_seats:
                db.commit()
                touched_events: set[str] = set()
                for seat in expired_seats:
                    event_id = str(seat.zone.event_id)
                    touched_events.add(event_id)
                    await connection_manager.broadcast(
                        event_id,
                        {
                            "type": "seat_status_changed",
                            "seat_id": seat.id,
                            "status": "AVAILABLE",
                        },
                    )
                for event_id in touched_events:
                    await DashboardService(db).broadcast_dashboard_update(event_id)
        except Exception as exc:
            db.rollback()
            logger.error("Failed to release expired holds: %s", exc, exc_info=True)
        finally:
            db.close()

        await asyncio.sleep(1)
