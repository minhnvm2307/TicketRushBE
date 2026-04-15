import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.redis import get_redis_client, redis_is_enabled


class QueueService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.redis = get_redis_client() if redis_is_enabled() else None

    def _queue_key(self, event_id: str) -> str:
        return f"queue:event:{event_id}"

    def _token_key(self, event_id: str, user_id: str) -> str:
        return f"queue:event:{event_id}:token:{user_id}"

    def join_or_status(self, event_id: str, user_id: str, active_visitors: int) -> dict:
        if not self.redis:
            return {"event_id": event_id, "bypass": True, "position": 0, "mode": "redis-disabled"}

        if active_visitors < self.settings.queue_threshold:
            return {"event_id": event_id, "bypass": True, "position": 0}

        token_key = self._token_key(event_id, user_id)
        existing_token = self.redis.get(token_key)
        if existing_token:
            ttl = self.redis.ttl(token_key)
            expires_at = datetime.now(UTC) + timedelta(seconds=max(ttl, 0))
            return {
                "event_id": event_id,
                "bypass": True,
                "position": 0,
                "access_token": existing_token,
                "expires_at": expires_at,
            }

        queue_key = self._queue_key(event_id)
        now_score = datetime.now(UTC).timestamp()
        self.redis.zadd(queue_key, {user_id: now_score}, nx=True)
        self._grant_batch(event_id)

        granted_token = self.redis.get(token_key)
        if granted_token:
            ttl = self.redis.ttl(token_key)
            expires_at = datetime.now(UTC) + timedelta(seconds=max(ttl, 0))
            return {
                "event_id": event_id,
                "bypass": True,
                "position": 0,
                "access_token": granted_token,
                "expires_at": expires_at,
            }

        rank = self.redis.zrank(queue_key, user_id)

        return {
            "event_id": event_id,
            "bypass": False,
            "position": (rank + 1) if rank is not None else 0,
            "access_token": None,
            "expires_at": None,
        }

    def _grant_batch(self, event_id: str) -> None:
        if not self.redis:
            return
        queue_key = self._queue_key(event_id)
        waiting_user_ids = self.redis.zrange(queue_key, 0, self.settings.queue_batch_size - 1)
        token_ttl = self.settings.queue_token_ttl_minutes * 60
        for queued_user_id in waiting_user_ids:
            token_key = self._token_key(event_id, queued_user_id)
            if self.redis.exists(token_key):
                self.redis.zrem(queue_key, queued_user_id)
                continue
            token = secrets.token_urlsafe(24)
            self.redis.set(token_key, token, ex=token_ttl)
            self.redis.zrem(queue_key, queued_user_id)
