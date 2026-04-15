import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import RedisKey, get_redis_client
from app.db.session import SessionLocal
from app.repositories.event import EventRepository

logger = logging.getLogger(__name__)


async def process_queues_job():
    """
    A background job that processes the waiting queues for all active events.
    It moves users from the waiting queue to the access list in batches.
    """
    db: Session = SessionLocal()
    redis = get_redis_client()
    settings = get_settings()
    event_repo = EventRepository(db)

    try:
        active_events = event_repo.list_active_for_queue_processing()
        logger.info(f"Found {len(active_events)} active events to process queues for.")

        for event in active_events:
            queue_key = RedisKey.event_queue(event.id)
            
            # Get the batch of users from the front of the queue
            users_to_process = redis.zpopmin(queue_key, settings.queue_batch_size)
            if not users_to_process:
                continue

            logger.info(f"Processing {len(users_to_process)} users for event {event.id}")

            # Use a pipeline to grant access tokens in a single transaction
            pipeline = redis.pipeline()
            for user_id, _ in users_to_process:
                access_key = RedisKey.event_access_token(event.id, user_id)
                pipeline.set(access_key, 1, ex=settings.queue_token_ttl_minutes * 60)
            
            pipeline.execute()
            logger.info(f"Granted access to {len(users_to_process)} users for event {event.id}")

    except Exception as e:
        logger.error(f"Error during queue processing job: {e}", exc_info=True)
    finally:
        db.close()


scheduler = AsyncIOScheduler(timezone="UTC")
scheduler.add_job(process_queues_job, "interval", seconds=10, id="process_queues_job")
