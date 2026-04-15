import json
from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


def redis_is_enabled() -> bool:
    return get_settings().enable_redis


def dumps_payload(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"))


def loads_payload(raw: str | None) -> dict | None:
    if not raw:
        return None
    return json.loads(raw)
