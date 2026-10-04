import redis.asyncio as aioredis
from .config import get_settings


def get_redis_client() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(
        settings.REDIS_URL.get_secret_value(),
        encoding="utf-8",
        decode_responses=True,
    )
