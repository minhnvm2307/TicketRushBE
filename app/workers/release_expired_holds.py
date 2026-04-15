from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.seats import SeatService

scheduler = BackgroundScheduler()


def release_expired_holds_job() -> None:
    db = SessionLocal()
    try:
        seat_service = SeatService(db)
        import asyncio

        asyncio.run(seat_service.release_expired())
    finally:
        db.close()


scheduler.add_job(release_expired_holds_job, "interval", seconds=60, id="release_expired_holds")
