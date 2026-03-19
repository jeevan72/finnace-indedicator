import time
import requests
from typing import Optional

from utils.nse_session import NSESessionManager
from utils.logger import get_logger
from utils.retry import retry
from utils.validators import validate_options_snapshot, ValidationError
from utils.time_utils import utc_now
from analysis.options_analytics import compute_pcr, compute_max_pain, extract_atm_iv, compute_iv_rank
from storage import models
from config.settings import CACHE_TTL_OPTIONS

logger = get_logger(__name__)

# Very simple TTL cache
_CACHE = {}

def get_from_cache(key: str):
    if key in _CACHE:
        val, expiry = _CACHE[key]
        if time.time() < expiry:
            return val
        else:
            del _CACHE[key]
    return None

def set_in_cache(key: str, val: dict, ttl: int):
    expiry = time.time() + ttl
    _CACHE[key] = (val, expiry)


@retry(max_attempts=3, backoff_factor=2.0)
def _fetch_options_chain_data(symbol: str) -> dict:
    """Uses NSESessionManager to get raw options JSON."""
    if symbol == "NIFTY" or symbol == "BANKNIFTY":
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    else:
        url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
    # The NSESessionManager automatically applies the strict rate limiting and session refresh logic
    response = NSESessionManager.fetch(url)
    return response.json()

def _get_historical_iv(symbol: str) -> list:
    """Retrieves 52W ATM IV history from the DB for IV Rank calculation."""
    records = models.OptionsSnapshot.select(models.OptionsSnapshot.atm_iv).where(
        (models.OptionsSnapshot.symbol == symbol) & 
        (models.OptionsSnapshot.atm_iv > 0)
    ).order_by(models.OptionsSnapshot.timestamp.desc()).limit(252) # approximated 52W trading days snapshot
    
    history = [r.atm_iv for r in records]
    return history if history else [15.0, 25.0] # Fallback mock range to prevent div/0 if DB is empty

def fetch_options_chain(symbol: str) -> Optional[dict]:
    """
    Fetches the NSE Option Chain for the given symbol and computes analytical metrics.
    Follows Section 17 Error Handling Contract. 
    """
    try:
        cached = get_from_cache(f"opts_{symbol}")
        if cached:
            return cached
            
        data = _fetch_options_chain_data(symbol)
        
        records = data.get("records", {})
        expiry_dates = records.get("expiryDates", [])
        if not expiry_dates:
            raise ValueError("No expiry dates found in NSE response")
            
        near_expiry = expiry_dates[0]
        
        # Filter data for only the nearest expiry
        chain_data = [d for d in records.get("data", []) if d.get("expiryDate") == near_expiry]
        underlying_val = records.get("underlyingValue", 0.0)
        
        pcr = compute_pcr(chain_data)
        max_pain = compute_max_pain(chain_data)
        atm_iv = extract_atm_iv(chain_data, underlying_val)
        
        iv_history = _get_historical_iv(symbol)
        iv_history.append(atm_iv) # Include current
        iv_rank = compute_iv_rank(atm_iv, iv_history)
        
        raw_record = {
            "symbol": symbol,
            "expiry": near_expiry, # usually like "27-Mar-2025" string format on NSE. We store as string/date, Peewee handles isoformat mapping ideally.
            "pcr": pcr,
            "max_pain": max_pain,
            "iv_rank": iv_rank,
            "atm_iv": atm_iv,
            "timestamp": utc_now().isoformat() + "Z"
        }
        
        validated = validate_options_snapshot(raw_record)
        
        # Insert raw options OI entries if requested by schema (fo_oi table)
        # However, the contract specifically states options_snapshot table is returned here. 
        # We save snapshot for brevity of Phase 1.
        # SQLite storage: format date for Sqlite
        from datetime import datetime
        try:
            # NSE date format is DD-MMM-YYYY, e.g. 24-Jul-2025
            iso_expiry = datetime.strptime(validated["expiry"], "%d-%b-%Y").strftime("%Y-%m-%d")
        except ValueError:
            iso_expiry = validated["expiry"]
            
        models.OptionsSnapshot.create(
            symbol=validated["symbol"],
            expiry=iso_expiry,
            pcr=validated["pcr"],
            max_pain=validated["max_pain"],
            iv_rank=validated["iv_rank"],
            atm_iv=validated["atm_iv"],
            timestamp=validated["timestamp"]
        )
        
        set_in_cache(f"opts_{symbol}", validated, ttl=CACHE_TTL_OPTIONS)
        return validated
        
    except ValidationError as e:
        logger.warning(f"[{__name__}] Validation failed for {symbol}: {e}")
        return _fallback_from_db(symbol)
        
    except (ConnectionError, TimeoutError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"[{__name__}] Network error for {symbol}: {e}")
        return _fallback_from_db(symbol)
        
    except Exception as e:
        logger.critical(f"[{__name__}] Unexpected error for {symbol}: {e}", exc_info=True)
        return _fallback_from_db(symbol)

def _fallback_from_db(symbol: str) -> Optional[dict]:
    """Return last known options snapshot from DB with staleness logic."""
    try:
        record = models.OptionsSnapshot.select().where(
            models.OptionsSnapshot.symbol == symbol
        ).order_by(models.OptionsSnapshot.timestamp.desc()).first()
        
        if record:
            result = {
                "symbol": record.symbol,
                "expiry": record.expiry.isoformat() if hasattr(record.expiry, 'isoformat') else str(record.expiry),
                "pcr": record.pcr,
                "max_pain": record.max_pain,
                "iv_rank": record.iv_rank,
                "atm_iv": record.atm_iv,
                "timestamp": record.timestamp.isoformat() + "Z" if hasattr(record.timestamp, 'isoformat') else str(record.timestamp),
                "stale": True
            }
            logger.warning(f"[{__name__}] Serving stale options data for {symbol}")
            return result
        return None
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback for options failed: {e}")
        return None
