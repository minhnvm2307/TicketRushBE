import asyncio
import logging

from app.db.session import SessionLocal
from app.repositories.event import EventRepository
from app.services.queue import QueueService

logger = logging.getLogger(__name__)


async def process_queues_job():
    while True:
        db = SessionLocal()
        try:
            service = QueueService()
            for event in EventRepository(db).list_active_for_queue_processing():
                service.process_event_queue(str(event.id))
        except ConnectionError:
            logger.debug("Queue worker skipped because Redis is disabled")
        except Exception as exc:
            logger.error("Failed to process virtual queue: %s", exc, exc_info=True)
        finally:
            db.close()

        await asyncio.sleep(1)
