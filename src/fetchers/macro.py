import time
import pandas as pd
from typing import Optional, List

from fredapi import Fred
import world_bank_data as wb

from config.settings import FRED_API_KEY, CACHE_TTL_MACRO
from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from utils.validators import validate_macro_series, ValidationError
from utils.time_utils import utc_now
from storage import models

logger = get_logger(__name__)

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

@rate_limit("fred")
@retry(max_attempts=3, backoff_factor=2)
def _fetch_fred_series(series_id: str) -> pd.Series:
    if not FRED_API_KEY or FRED_API_KEY == "your_fred_key_here":
        raise ValueError("FRED_API_KEY is not configured.")
    fred = Fred(api_key=FRED_API_KEY)
    return fred.get_series(series_id)

@rate_limit("worldbank")
@retry(max_attempts=3, backoff_factor=2)
def _fetch_wb_series(indicator: str, country: str) -> pd.Series:
    # returns a multi-index series
    return wb.get_series(indicator, country=country)

def fetch_macro_indicators() -> List[dict]:
    """
    Fetches the configured macro economic indicators from FRED and World Bank.
    """
    cache_key = "macro_indicators"
    cached = get_from_cache(cache_key)
    if cached:
        return cached

    results = []

    # Mapping
    fred_series = [
        ("CPIAUCSL", "US CPI YoY", "US"),
        ("DGS10", "US 10Y Treasury Yield", "US"),
        ("INTDSRINM193N", "India Interest Rate (Discount)", "IN")
    ]
    
    wb_series = [
        ("NY.GDP.MKTP.KD.ZG", "India GDP YoY", "IN")
    ]

    for sid, sname, country in fred_series:
        try:
            series = _fetch_fred_series(sid)
            series = series.dropna()
            
            if series.empty:
                continue
                
            last_date = series.index[-1]
            last_val = series.iloc[-1]
            
            raw = {
                "indicator_code": sid,
                "indicator_name": sname,
                "country": country,
                "value": float(last_val),
                "period": last_date.strftime("%Y-%m-%d") if hasattr(last_date, "strftime") else str(last_date),
                "timestamp": utc_now().isoformat() + "Z",
                "source": "FRED"
            }
            validated = validate_macro_series(raw)
            results.append(validated)
            
            models.MacroSeries.create(**validated)
        except Exception as e:
            logger.error(f"[{__name__}] Failed fetching FRED {sid}: {e}")
            res = _fallback_from_db(sid)
            if res: results.append(res)
            
    for sid, sname, country in wb_series:
        try:
            # Country codes like IN, USA works for WB, but IND is standard
            c_code = "IND" if country == "IN" else "USA"
            series = _fetch_wb_series(sid, c_code)
            series = series.dropna()
            
            if series.empty:
                continue
                
            # Series is indexed by (Country, Year). We need the last valid year.
            last_idx = series.index[-1]
            last_year = last_idx[2] if len(last_idx) > 2 else last_idx[1] if len(last_idx) > 1 else last_idx
            last_val = series.iloc[-1]
            
            raw = {
                "indicator_code": sid,
                "indicator_name": sname,
                "country": country,
                "value": float(last_val),
                "period": str(last_year),
                "timestamp": utc_now().isoformat() + "Z",
                "source": "World Bank"
            }
            validated = validate_macro_series(raw)
            results.append(validated)
            
            models.MacroSeries.create(**validated)
        except Exception as e:
            logger.error(f"[{__name__}] Failed fetching WB {sid}: {e}")
            res = _fallback_from_db(sid)
            if res: results.append(res)

    set_in_cache(cache_key, results, CACHE_TTL_MACRO)
    return results

def _fallback_from_db(indicator_code: str) -> Optional[dict]:
    """Retrieves the last known macro snapshot from SQLite."""
    try:
        record = models.MacroSeries.select().where(
            models.MacroSeries.indicator_code == indicator_code
        ).order_by(models.MacroSeries.timestamp.desc()).first()
        
        if record:
            return {
                "indicator_code": record.indicator_code,
                "indicator_name": record.indicator_name,
                "country": record.country,
                "value": record.value,
                "period": record.period,
                "timestamp": record.timestamp.isoformat() + "Z" if hasattr(record.timestamp, 'isoformat') else str(record.timestamp),
                "source": record.source,
                "stale": True,
                "delay_note": "[STALE - DB FALLBACK]"
            }
        return None
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback failed for {indicator_code}: {e}")
        return None
