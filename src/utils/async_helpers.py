"""
Async helpers for concurrent data fetching.
Provides semaphore-based concurrency limiting and async retry logic.
"""
import asyncio
import functools
import time
from typing import Callable, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Global semaphore to limit concurrent API calls
_API_SEMAPHORE = asyncio.Semaphore(5)


async def limited_gather(*coroutines, max_concurrent: int = 5):
    """
    Run multiple coroutines concurrently with a concurrency limit.
    Returns results in the same order as the input coroutines.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[limited(c) for c in coroutines], return_exceptions=True)


def async_retry(max_attempts: int = 3, backoff_factor: float = 1.5):
    """Async-compatible retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait = backoff_factor ** attempt
                        logger.warning(
                            f"[async_retry] {func.__name__} attempt {attempt}/{max_attempts} "
                            f"failed: {e}. Retrying in {wait:.1f}s..."
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(
                            f"[async_retry] {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator


class AsyncRateLimiter:
    """Token-bucket rate limiter for async functions."""
    
    def __init__(self, calls_per_second: float = 2.0):
        self._min_interval = 1.0 / calls_per_second
        self._last_call = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


# Pre-configured rate limiters per API source
_rate_limiters = {
    "yahoo_finance": AsyncRateLimiter(calls_per_second=2.0),
    "nse_india": AsyncRateLimiter(calls_per_second=1.0),
    "bse_india": AsyncRateLimiter(calls_per_second=1.0),
    "fred": AsyncRateLimiter(calls_per_second=1.0),
}


def get_rate_limiter(source: str) -> AsyncRateLimiter:
    """Get or create a rate limiter for a given API source."""
    if source not in _rate_limiters:
        _rate_limiters[source] = AsyncRateLimiter(calls_per_second=1.0)
    return _rate_limiters[source]
