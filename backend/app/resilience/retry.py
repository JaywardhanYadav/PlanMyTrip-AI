import asyncio
import random
from collections.abc import Callable, Coroutine
from typing import TypeVar

T = TypeVar("T")


async def with_retry(
    func: Callable[[], Coroutine[object, object, T]],
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> T:
    delay = initial_delay
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as exc:
            last_exception = exc
            if attempt == max_retries - 1:
                break
            sleep_time = delay * (1 + random.random() * 0.1) if jitter else delay
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop exited without result or exception")
