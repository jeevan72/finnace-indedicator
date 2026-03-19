import time
import requests
from utils.logger import get_logger
from utils.rate_limiter import rate_limit

logger = get_logger(__name__)

class NSESessionManager:
    """
    Manages NSE session cookies and headers as per Section 4 of requirements.
    This singleton ensures cookies are fetched from the homepage first and 
    properly reused across fetchers.
    """
    _session = None
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com"
    }

    @classmethod
    def get_session(cls) -> requests.Session:
        if cls._session is None:
            cls._create_new_session()
        return cls._session

    @classmethod
    def _create_new_session(cls):
        logger.info("[NSE Session] Initializing new NSE Session to acquire cookies...")
        cls._session = requests.Session()
        cls._session.headers.update(cls._headers)
        try:
            # First GET must go to homepage to get the requisite routing cookies
            cls._session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            logger.error(f"[NSE Session] Failed to fetch NSE homepage: {e}")

    @classmethod
    @rate_limit("nse_india")
    def fetch(cls, url: str) -> requests.Response:
        """
        Fetches an endpoint from NSE with up to 3 session refresh attempts on 401/403 blocks.
        Applies a rate limit decorator to strictly adhere to the ~30 req/min rule.
        """
        for attempt in range(1, 4):
            session = cls.get_session()
            logger.debug(f"[NSE] GET {url} (Attempt {attempt})")
            
            try:
                resp = session.get(url, timeout=10)
                
                if resp.status_code in (401, 403):
                    logger.warning(f"[NSE] {resp.status_code} block on attempt {attempt}. Refreshing session...")
                    cls._session = None  # Force recreate on next loop
                    time.sleep(1.5)      # Required 1.5s delay between consecutive NSE calls
                    continue
                    
                resp.raise_for_status()
                # 1.5s delay enforcement is also handled by @rate_limit, but added safety margin
                time.sleep(1.5) 
                
                return resp
                
            except requests.exceptions.HTTPError as e:
                # If it's 429 or 5xx, raise for standard outer retry logic wrapper
                if e.response.status_code not in (401, 403):
                    raise
            except requests.exceptions.RequestException as e:
                # Network error, let outer decorator retry
                raise
                
        raise ConnectionError(f"Failed to fetch {url} after 3 session refreshes.")
