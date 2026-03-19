import time
from functools import wraps
from config.rate_limits import RATE_LIMITS

# Shared state to track last calls across different modules calling the same limit
_LAST_CALLED = {}

def rate_limit(source: str, calls: int = None, period: float = None):
    """
    Ensures safe rate limit spacing per API source.
    Pulls limit defined in config/rate_limits.py if not manually provided.
    """
    global _LAST_CALLED
    
    if source in RATE_LIMITS:
        cfg_calls, cfg_period = RATE_LIMITS[source]
        calls = calls or cfg_calls
        period = period or cfg_period
    
    if calls is None or period is None:
        raise ValueError("Must provide either a known source or calls/period")
        
    min_interval = period / float(calls)
    
    if source not in _LAST_CALLED:
        _LAST_CALLED[source] = 0.0
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - _LAST_CALLED[source]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
                
            ret = func(*args, **kwargs)
            _LAST_CALLED[source] = time.time()
            return ret
        return wrapper
    return decorator
