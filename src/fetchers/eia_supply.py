import time
import requests
from typing import Optional, List

from config.settings import EIA_API_KEY, CACHE_TTL_MACRO
from config.constants import SUPPLY_THRESHOLDS
from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from utils.validators import validate_supply_event, ValidationError
from utils.time_utils import utc_now
from storage import models

logger = get_logger(__name__)

# Basic memory cache
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

@rate_limit("eia")
@retry(max_attempts=3, backoff_factor=2)
def _call_eia_api() -> dict:
    if not EIA_API_KEY or EIA_API_KEY == "your_eia_key_here":
        raise ValueError("EIA_API_KEY is not configured.")
        
    # U.S. Ending Stocks of Crude Oil (Weekly)
    # Using EIA API v2 route
    url = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[series][]": "WCESTUS1", # US Crude Oil Excluding SPR Ending Stocks
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 2 # We only need last week and previous week to compute WoW change
    }
    
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch_eia_crude_inventory() -> Optional[dict]:
    """
    Fetches the latest Crude Oil Inventory WoW change from EIA.
    Generates a SupplyEvent summarizing if the change is bullish/bearish/neutral.
    """
    cache_key = "eia_crude_wstk"
    cached = get_from_cache(cache_key)
    if cached:
        return cached

    try:
        data = _call_eia_api()
        records = data.get("response", {}).get("data", [])
        
        if len(records) < 2:
            raise ValueError("EIA API did not return enough historical data to compute WoW change.")
            
        current_week = records[0]
        prev_week = records[1]
        
        # Values are in Thousand Barrels. Convert to Millions of Barrels (MMBbl)
        current_val = float(current_week.get("value", 0)) / 1000.0
        prev_val = float(prev_week.get("value", 0)) / 1000.0
        
        wow_change = round(current_val - prev_val, 2)
        
        # Analyze Signal
        signal = "neutral"
        if wow_change <= -SUPPLY_THRESHOLDS["eia_crude_draw_bullish_mmbbl"]:
            signal = "bullish"
        elif wow_change >= SUPPLY_THRESHOLDS["eia_crude_build_bearish_mmbbl"]:
            signal = "bearish"
            
        raw_record = {
            "commodity": "Crude Oil",
            "event_type": "EIA Inventory WoW Change",
            "value": wow_change,
            "unit": "MMBbl",
            "signal": signal,
            "timestamp": utc_now().isoformat() + "Z",
            "source": "EIA API v2"
        }
        
        validated = validate_supply_event(raw_record)
        
        # Store in DB
        models.SupplyEvents.create(
            commodity=validated["commodity"],
            event_type=validated["event_type"],
            value=validated["value"],
            unit=validated["unit"],
            signal=validated["signal"],
            timestamp=validated["timestamp"],
            source=validated["source"]
        )
        
        set_in_cache(cache_key, validated, CACHE_TTL_MACRO)
        return validated

    except ValidationError as e:
        logger.warning(f"[{__name__}] EIA Schema Validation failed: {e}")
        return _fallback_from_db("Crude Oil")
        
    except Exception as e:
        logger.error(f"[{__name__}] EIA API Fetch Failed: {e}", exc_info=True)
        return _fallback_from_db("Crude Oil")


def _fallback_from_db(commodity: str) -> Optional[dict]:
    """Retrieves the last known supply event for a commodity from SQLite."""
    try:
        record = models.SupplyEvents.select().where(
            models.SupplyEvents.commodity == commodity
        ).order_by(models.SupplyEvents.timestamp.desc()).first()
        
        if record:
            return {
                "commodity": record.commodity,
                "event_type": record.event_type,
                "value": record.value,
                "unit": record.unit,
                "signal": record.signal,
                "timestamp": record.timestamp.isoformat() + "Z" if hasattr(record.timestamp, 'isoformat') else str(record.timestamp),
                "source": record.source,
                "stale": True,
                "delay_note": "[STALE - DB FALLBACK]"
            }
        return None
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback failed: {e}")
        return None
