import json
from collections.abc import Callable, Coroutine
from typing import TypeVar
import redis.asyncio as aioredis
from ..core.redis_client import get_redis_client

T = TypeVar("T")


class ResponseCache:
    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl = default_ttl_seconds
        self.redis: aioredis.Redis | None = None

    def _get_client(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = get_redis_client()
        return self.redis

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Coroutine[object, object, T]],
        ttl: int | None = None,
    ) -> T:
        client = self._get_client()
        expire = ttl or self.default_ttl

        try:
            cached = await client.get(key)
            if cached is not None:
                return json.loads(cached)  # type: ignore[no-any-return]
        except Exception:
            pass

        result = await factory()

        try:
            serialized = json.dumps(result)
            await client.set(key, serialized, ex=expire)
        except Exception:
            pass

        return result
