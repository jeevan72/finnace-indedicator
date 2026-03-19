"""
Unified cache module with Redis support and in-memory fallback.
Falls back gracefully to dict-based cache if Redis is unavailable.
"""
import json
import time
from typing import Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)

_redis_client = None
_memory_cache = {}


def _get_redis():
    """Lazy-init Redis connection. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        client.ping()
        _redis_client = client
        logger.info("[cache] Connected to Redis successfully")
        return _redis_client
    except Exception:
        logger.info("[cache] Redis not available, using in-memory fallback")
        return None


def get(key: str) -> Optional[dict]:
    """Get a cached value. Tries Redis first, falls back to memory."""
    r = _get_redis()
    if r:
        try:
            val = r.get(f"fit:{key}")
            if val:
                return json.loads(val)
        except Exception as e:
            logger.debug(f"[cache] Redis GET failed: {e}")
    
    # In-memory fallback
    if key in _memory_cache:
        val, expiry = _memory_cache[key]
        if time.time() < expiry:
            return val
        else:
            del _memory_cache[key]
    return None


def set(key: str, value: Any, ttl: int = 300):
    """Set a cached value with TTL (seconds). Stores in both Redis and memory."""
    r = _get_redis()
    if r:
        try:
            r.setex(f"fit:{key}", ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.debug(f"[cache] Redis SET failed: {e}")
    
    # Always store in memory as fallback
    _memory_cache[key] = (value, time.time() + ttl)


def delete(key: str):
    """Delete a cached key from both stores."""
    r = _get_redis()
    if r:
        try:
            r.delete(f"fit:{key}")
        except Exception:
            pass
    _memory_cache.pop(key, None)


def clear():
    """Clear all cached keys."""
    r = _get_redis()
    if r:
        try:
            for k in r.scan_iter("fit:*"):
                r.delete(k)
        except Exception:
            pass
    _memory_cache.clear()
