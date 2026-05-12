import time

from redis import Redis

from app.core.config import get_settings
from app.core.redis import RedisKey, get_redis_client, redis_is_enabled
from app.schemas.queue import QueueStatus


class QueueService:
    def __init__(self) -> None:
        if not redis_is_enabled():
            raise ConnectionError("Redis is not enabled or connected")
        self.redis: Redis = get_redis_client()
        self.settings = get_settings()

    def get_queue_status(self, event_id: str, user_id: str) -> QueueStatus:
        """
        Checks the user's status in the queue for a specific event.
        """
        queue_key = RedisKey.event_queue(event_id)
        access_key = RedisKey.event_access_token(event_id, user_id)
        checkout_key = RedisKey.checkout_access(event_id, user_id)
        str_user_id = str(user_id)

        # Check if user has active access
        access_ttl = self.redis.ttl(access_key)
        checkout_ttl = self.redis.ttl(checkout_key)
        if access_ttl > 0:
            return QueueStatus(
                position=0,
                total_users=self.redis.zcard(queue_key),
                is_in_queue=False,
                has_access=True,
                can_checkout=True,
                access_expires_in=access_ttl,
                checkout_expires_in=checkout_ttl if checkout_ttl > 0 else None,
            )

        if checkout_ttl > 0:
            return QueueStatus(
                position=0,
                total_users=self.redis.zcard(queue_key),
                is_in_queue=False,
                has_access=False,
                can_checkout=True,
                access_expires_in=None,
                checkout_expires_in=checkout_ttl,
            )

        # Check user's position in the queue
        rank = self.redis.zrank(queue_key, str_user_id)
        total_in_queue = self.redis.zcard(queue_key)

        if rank is not None:
            return QueueStatus(
                position=rank + 1,
                total_users=total_in_queue,
                is_in_queue=True,
                has_access=False,
                can_checkout=False,
            )

        return QueueStatus(
            position=0,
            total_users=total_in_queue,
            is_in_queue=False,
            has_access=False,
            can_checkout=False,
        )

    def join_queue(self, event_id: str, user_id: str) -> QueueStatus:
        """
        Adds a user to the event queue if they are not already in it or have access.
        """
        status = self.get_queue_status(event_id, user_id)
        if status.is_in_queue or status.has_access:
            return status

        # Add user to the sorted set with the current timestamp as score
        queue_key = RedisKey.event_queue(event_id)
        self.redis.zadd(queue_key, {str(user_id): time.time()})

        return self.get_queue_status(event_id, user_id)
