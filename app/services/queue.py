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

    def _active_access_count(self, event_id: str) -> int:
        pattern = RedisKey.booking_session(str(event_id), "*")
        return sum(1 for _ in self.redis.scan_iter(match=pattern))

    def get_queue_status(self, event_id: str, user_id: str) -> QueueStatus:
        session_key = RedisKey.booking_session(str(event_id), str(user_id))
        active_users = self._active_access_count(event_id)
        max_active_users = self.settings.queue_threshold

        session_ttl = self.redis.ttl(session_key)
        if session_ttl > 0:
            return QueueStatus(
                active_users=active_users,
                max_active_users=max_active_users,
                has_access=True,
                session_expires_in=session_ttl,
            )

        return QueueStatus(
            active_users=active_users,
            max_active_users=max_active_users,
            has_access=False,
            notice="Seat selection room is currently full. Please try again in a moment.",
        )

    def join_queue(self, event_id: str, user_id: str) -> QueueStatus:
        status = self.get_queue_status(event_id, user_id)
        if status.has_access:
            return status

        if self.settings.queue_threshold <= 0 or status.active_users < self.settings.queue_threshold:
            self.redis.set(
                RedisKey.booking_session(str(event_id), str(user_id)),
                1,
                ex=self.settings.queue_token_ttl_minutes * 60,
            )
            return self.get_queue_status(event_id, user_id)

        return status
