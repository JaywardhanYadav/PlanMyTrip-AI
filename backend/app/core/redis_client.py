from typing import Any
import redis.asyncio as aioredis
from .config import get_settings


def get_redis_client() -> Any:
    settings = get_settings()
    from_url_fn = getattr(aioredis, "from_url")
    return from_url_fn(
        settings.REDIS_URL.get_secret_value(),
        encoding="utf-8",
        decode_responses=True,
    )
