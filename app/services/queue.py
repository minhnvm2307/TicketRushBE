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

    def _active_access_count(self, event_id: str) -> int:
        pattern = RedisKey.booking_session(str(event_id), "*")
        return sum(1 for _ in self.redis.scan_iter(match=pattern))

    def _queue_position(self, event_id: str, user_id: str) -> int | None:
        rank = self.redis.zrank(RedisKey.event_queue(str(event_id)), str(user_id))
        return int(rank) + 1 if rank is not None else None

    def _queue_size(self, event_id: str) -> int:
        return int(self.redis.zcard(RedisKey.event_queue(str(event_id))))

    def _session_ttl(self, event_id: str, user_id: str) -> int:
        return int(self.redis.ttl(RedisKey.booking_session(str(event_id), str(user_id))))

    def _grant_access(self, event_id: str, user_id: str) -> None:
        self.redis.set(
            RedisKey.booking_session(str(event_id), str(user_id)),
            1,
            ex=self.settings.queue_token_ttl_minutes * 60,
        )
        self.redis.zrem(RedisKey.event_queue(str(event_id)), str(user_id))

    def _can_grant_access(self, event_id: str) -> bool:
        return self.settings.queue_threshold <= 0 or (
            self._active_access_count(event_id) < self.settings.queue_threshold
        )

    def _promote_user_if_ready(self, event_id: str, user_id: str) -> None:
        if not self._can_grant_access(event_id):
            return
        position = self._queue_position(event_id, user_id)
        if position == 1:
            self._grant_access(event_id, user_id)

    def get_queue_status(self, event_id: str, user_id: str) -> QueueStatus:
        event_id = str(event_id)
        user_id = str(user_id)
        max_active_users = self.settings.queue_threshold

        session_ttl = self._session_ttl(event_id, user_id)
        if session_ttl > 0:
            self.redis.zrem(RedisKey.event_queue(event_id), user_id)
            return QueueStatus(
                active_users=self._active_access_count(event_id),
                max_active_users=max_active_users,
                has_access=True,
                session_expires_in=session_ttl,
                queue_size=self._queue_size(event_id),
            )

        self._promote_user_if_ready(event_id, user_id)
        session_ttl = self._session_ttl(event_id, user_id)
        if session_ttl > 0:
            return QueueStatus(
                active_users=self._active_access_count(event_id),
                max_active_users=max_active_users,
                has_access=True,
                session_expires_in=session_ttl,
                queue_size=self._queue_size(event_id),
                notice="Access granted. You can select seats now.",
            )

        position = self._queue_position(event_id, user_id)
        queue_size = self._queue_size(event_id)
        active_users = self._active_access_count(event_id)
        if position is not None:
            return QueueStatus(
                active_users=active_users,
                max_active_users=max_active_users,
                has_access=False,
                queue_position=position,
                queue_size=queue_size,
                notice=(
                    f"Your position is {position}/{queue_size}. "
                    f"The seat room limit is {max_active_users}. Please do not reload this page."
                ),
            )

        return QueueStatus(
            active_users=active_users,
            max_active_users=max_active_users,
            has_access=False,
            queue_size=queue_size,
            notice="Seat selection room is full. Join the queue to wait for the next slot.",
        )

    def join_queue(self, event_id: str, user_id: str) -> QueueStatus:
        event_id = str(event_id)
        user_id = str(user_id)
        status = self.get_queue_status(event_id, user_id)
        if status.has_access:
            return status

        queue_key = RedisKey.event_queue(event_id)
        if status.queue_position is None:
            if self._can_grant_access(event_id) and self._queue_size(event_id) == 0:
                self._grant_access(event_id, user_id)
                return self.get_queue_status(event_id, user_id)
            self.redis.zadd(queue_key, {user_id: time.time()}, nx=True)

        return self.get_queue_status(event_id, user_id)

    def process_event_queue(self, event_id: str) -> int:
        event_id = str(event_id)
        promoted = 0
        max_active_users = self.settings.queue_threshold

        if max_active_users <= 0:
            free_slots = self.settings.queue_batch_size
        else:
            free_slots = max_active_users - self._active_access_count(event_id)

        if free_slots <= 0:
            return 0

        for user_id in self.redis.zrange(RedisKey.event_queue(event_id), 0, free_slots - 1):
            if self._session_ttl(event_id, user_id) > 0:
                self.redis.zrem(RedisKey.event_queue(event_id), user_id)
                continue
            self._grant_access(event_id, user_id)
            promoted += 1
            if promoted >= self.settings.queue_batch_size:
                break

        return promoted
