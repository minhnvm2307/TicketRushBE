import json
from functools import lru_cache
from typing import Any

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def redis_is_enabled() -> bool:
    return get_settings().enable_redis


def dumps_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"))


def loads_payload(raw: str | bytes | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return json.loads(raw)


class RedisKey:
    @staticmethod
    def seat_lock(event_id: str, seat_id: str) -> str:
        return f"ticketrush:event:{event_id}:seat:{seat_id}:lock"

    @staticmethod
    def event_queue(event_id: str) -> str:
        return f"ticketrush:event:{event_id}:queue"

    @staticmethod
    def event_access_token(event_id: str, user_id: str) -> str:
        return f"ticketrush:event:{event_id}:access_token:{user_id}"
