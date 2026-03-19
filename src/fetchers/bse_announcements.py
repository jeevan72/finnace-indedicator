import time
import requests
import re
from typing import List, Optional

from config.constants import ANNOUNCEMENT_KEYWORDS
from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from utils.time_utils import utc_now
from storage import models

logger = get_logger(__name__)

def _match_keywords(headline: str) -> Optional[tuple]:
    """
    Checks if the headline contains any of the tracked corporate action keywords.
    Returns (event_category_name, matched_keyword_string) if a match is found.
    """
    headline_lower = headline.lower()
    for category, keywords in ANNOUNCEMENT_KEYWORDS.items():
        for kw in keywords:
            # use regex word boundary for exact matches
            if re.search(rf"\b{re.escape(kw)}\b", headline_lower):
                return category, kw
    return None

@rate_limit("bse_india")
@retry(max_attempts=3, backoff_factor=2)
def _call_bse_api(scrip_code: str) -> dict:
    # Typical undocumented BSE endpoint for corporate announcements
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
    params = {
        "pageno": 1,
        "strCat": -1,
        "strPrevDate": "",
        "strScrip": scrip_code,
        "strSearch": "P",
        "strToDate": "",
        "strType": "C"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.bseindia.com",
        "Referer": "https://www.bseindia.com/"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_bse_announcements(symbol: str, scrip_code: str) -> List[dict]:
    """
    Fetches raw corporate announcements from BSE and filters them against 
    our ANNOUNCEMENT_KEYWORDS matrix for AGMs, results, splits, etc.
    """
    results = []
    try:
        data = _call_bse_api(scrip_code)
        # BSE responses are notoriously inconsistent. Assume key 'Table'
        announcements = data.get("Table", [])
        
        for item in announcements:
            headline = item.get("HEADLINE", "")
            match = _match_keywords(headline)
            
            if match:
                category, kw = match
                dt_str = item.get("NEWS_DT", "")
                
                # We save it as an Event record
                raw = {
                    "symbol": symbol,
                    "event_type": category,
                    "headline": headline[:500],
                    "keywords_matched": kw,
                    "source": "BSE India",
                    "timestamp": utc_now().isoformat() + "Z" 
                }
                
                # Check duplication by headline + symbol
                exists = models.Events.select().where(
                    (models.Events.symbol == symbol) &
                    (models.Events.headline == raw["headline"])
                ).exists()
                
                if not exists:
                    models.Events.create(**raw)
                    results.append(raw)
                    
        return results
        
    except Exception as e:
        logger.error(f"[{__name__}] BSE Announcement fetch failed for {symbol}: {e}")
        return _fallback_from_db(symbol)

def _fallback_from_db(symbol: str) -> List[dict]:
    """Pulls the latest known significant events from local DB on network failure."""
    try:
        records = models.Events.select().where(
            models.Events.symbol == symbol
        ).order_by(models.Events.timestamp.desc()).limit(5)
        
        return [{
            "symbol": r.symbol,
            "event_type": r.event_type,
            "headline": r.headline,
            "keywords_matched": r.keywords_matched,
            "source": r.source,
            "timestamp": r.timestamp.isoformat() + "Z" if hasattr(r.timestamp, 'isoformat') else str(r.timestamp),
            "stale": True
        } for r in records]
    except Exception as e:
        logger.critical(f"[{__name__}] DB rollback failed for BSE events {symbol}: {e}")
        return []
