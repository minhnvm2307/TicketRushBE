import json
from functools import lru_cache
from typing import Any

from redis import Redis
from fastapi.encoders import jsonable_encoder

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def redis_is_enabled() -> bool:
    return get_settings().enable_redis


def dumps_payload(payload: dict[str, Any]) -> str:
    # Ensure non-JSON-native types (UUID, datetime, Decimal, etc.) are encoded.
    return json.dumps(jsonable_encoder(payload), separators=(",", ":"))


def loads_payload(raw: str | bytes | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return json.loads(raw)


class RedisKey:
    @staticmethod
    def auth_session(session_id: str) -> str:
        return f"ticketrush:auth:session:{session_id}"

    @staticmethod
    def seat_lock(event_id: str, seat_id: str) -> str:
        return f"ticketrush:event:{event_id}:seat:{seat_id}:lock"

    @staticmethod
    def event_queue(event_id: str) -> str:
        return f"ticketrush:event:{event_id}:queue"

    @staticmethod
    def booking_session(event_id: str, user_id: str) -> str:
        return f"ticketrush:event:{event_id}:booking_session:{user_id}"

    @staticmethod
    def user_event_hold_index(user_id: str, event_id: str) -> str:
        return f"ticketrush:user:{user_id}:event:{event_id}:holds"
