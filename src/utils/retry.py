import time
from functools import wraps
import requests

# Exception types that trigger retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    # Need to handle specific HTTP errors inside the wrapper manually 
    # since requests.exceptions.HTTPError often wraps 401s which we shouldn't retry without custom logic. 
)

def retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    """
    Retries an operation on network errors or 5xx/429 HTTP statuses.
    Wait times: 1s, 2s, 4s...
    Does NOT retry on 401, 403, or custom ValidationErrors.
    """
    def decorator(func):
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1.0
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    # Retry on 429 or 5xx
                    status = e.response.status_code
                    if status in (429, 500, 502, 503, 504):
                        if attempt == max_attempts:
                            raise
                        logger.warning(f"Retryable HTTP {status} error on attempt {attempt}. Retrying in {delay}s...")
                    else:
                        # e.g., 401, 403, 404 should just raise immediately.
                        raise
                except RETRYABLE_EXCEPTIONS as e:
                    if attempt == max_attempts:
                        raise
                    logger.warning(f"Retryable network error {type(e).__name__} on attempt {attempt}. Retrying in {delay}s...")
                
                # Execute delay and grow backoff
                time.sleep(delay)
                delay *= backoff_factor
            
            return None
        return wrapper
    return decorator
