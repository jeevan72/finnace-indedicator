import time
import requests
import yfinance as yf
from typing import Optional

from config.settings import CACHE_TTL_PRICES
from config.assets import YF_TICKERS, IS_DELAYED_MONTHLY
from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from utils.validators import validate_price_record, ValidationError
from utils.time_utils import utc_now
from storage import models

logger = get_logger(__name__)

# Assets whose prices are quoted in USD and need INR conversion
USD_ASSETS = {"Gold", "Silver", "Copper", "Nickel", "WTI Crude", "Brent Crude", "Natural Gas", "Coal"}

# Precious metals: convert from per-troy-oz to per-10-grams (Indian standard)
PRECIOUS_METALS_PER_10G = {"Gold", "Silver"}
TROY_OZ_TO_GRAMS = 31.1035
INDIA_GOLD_PREMIUM = 1.11  # ~11% (import duty 12.5% + GST 3% - adjustments)

# Assets that are natively in INR (no conversion needed)
INR_NATIVE_ASSETS = {"Nifty", "Sensex", "India VIX"}

# Simple in-memory dict cache as dictated by Section 7.9
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

def get_usd_inr_rate() -> float:
    """Fetches the live USD/INR exchange rate with a 5-minute cache."""
    cached = get_from_cache("_usd_inr_rate")
    if cached:
        return cached
    try:
        ticker = yf.Ticker("INR=X")
        info = ticker.fast_info
        rate = info.get('lastPrice') or info.last_price
        if rate and rate > 0:
            set_in_cache("_usd_inr_rate", float(rate), ttl=300)  # 5 min cache
            logger.info(f"[{__name__}] USD/INR rate fetched: {rate}")
            return float(rate)
    except Exception as e:
        logger.warning(f"[{__name__}] Failed to fetch USD/INR rate: {e}")
    # Fallback to a reasonable default if API fails
    logger.warning(f"[{__name__}] Using fallback USD/INR rate of 83.0")
    return 83.0

@retry(max_attempts=3, backoff_factor=2.0)
@rate_limit("yahoo_finance") 
def _call_yf_api(symbol_name: str, symbol_ticker: str) -> dict:
    """Make the actual network call to yfinance."""
    ticker = yf.Ticker(symbol_ticker)
    
    try:
        info = ticker.fast_info
        current_price = info.get('lastPrice') or info.last_price
        prev_close = info.get('previousClose') or info.previous_close
    except Exception as e:
        logger.debug(f"[{__name__}] Fast info failed for {symbol_ticker}: {e}. Falling back to history.")
        hist = ticker.history(period="1d")
        if hist.empty:
            raise ValueError(f"No valid data returned for {symbol_ticker}")
        current_price = float(hist['Close'].iloc[-1])
        open_price = float(hist['Open'].iloc[-1])
        prev_close = open_price # Approximation
        
    if current_price and prev_close and prev_close > 0:
        change_pct = ((current_price - prev_close) / prev_close) * 100
    else:
        change_pct = 0.0
        
    is_delayed = symbol_name in IS_DELAYED_MONTHLY
    
    # Convert USD-denominated assets to INR
    price_value = float(current_price)
    display_name = symbol_name
    if symbol_name in USD_ASSETS:
        usd_inr = get_usd_inr_rate()
        price_value = price_value * usd_inr
        
        # Convert precious metals from per-troy-oz to per-10-grams (Indian standard)
        if symbol_name in PRECIOUS_METALS_PER_10G:
            price_per_gram = price_value / TROY_OZ_TO_GRAMS
            price_value = price_per_gram * 10 * INDIA_GOLD_PREMIUM
            display_name = f"{symbol_name} (10g)"
        
        currency = "INR"
    elif symbol_name in INR_NATIVE_ASSETS:
        currency = "INR"
    else:
        currency = "USD"  # FX pairs, DXY, VIX etc. stay in their native unit
    
    return {
        "symbol": symbol_name,
        "name": display_name,
        "price": price_value,
        "change_pct": float(change_pct),
        "volume": None, 
        "timestamp": utc_now().isoformat() + "Z",
        "source": "yahoo_finance",
        "is_delayed": is_delayed,
        "currency": currency,
        "delay_note": "[DELAYED - MONTHLY] LME Avg" if is_delayed else None
    }

def fetch_price(symbol: str) -> Optional[dict]:
    """
    Fetches price from yFinance.
    Implements Section 17 Error Handling Contract completely.
    """
    try:
        cached = get_from_cache(symbol)
        if cached:
            return cached
            
        ticker = YF_TICKERS.get(symbol)
        if not ticker:
            logger.warning(f"[{__name__}] Symbol {symbol} not found in config/assets.py maps")
            return None
            
        raw = _call_yf_api(symbol, ticker)
        validated = validate_price_record(raw)
        
        # Save validated data to DB
        # Removing delay_note from **kwargs insertion if it's not in the Price schema
        db_insert_data = {k: v for k, v in validated.items() if k not in ("delay_note",)} 
        models.Prices.create(**db_insert_data)
        
        set_in_cache(symbol, validated, ttl=CACHE_TTL_PRICES)
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
    """Return last known value from DB with staleness flag per Section 17."""
    try:
        record = models.Prices.select().where(
            models.Prices.symbol == symbol
        ).order_by(models.Prices.timestamp.desc()).first()
        
        if record:
            result = {
                "symbol": record.symbol,
                "name": record.name,
                "price": record.price,
                "change_pct": record.change_pct,
                "volume": record.volume,
                "timestamp": record.timestamp.isoformat() + "Z" if hasattr(record.timestamp, 'isoformat') else str(record.timestamp),
                "source": record.source,
                "is_delayed": record.is_delayed,
                "delay_note": "[STALE - DB FALLBACK]"
            }
            result['stale'] = True
            logger.warning(f"[{__name__}] Serving stale data for {symbol}")
            return result
        return None
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback failed for {symbol}: {e}")
        return None


# ──────────────────────── Async Batch Fetching ────────────────────────
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Shared thread pool for running sync yfinance calls in async context
_executor = ThreadPoolExecutor(max_workers=5)


async def fetch_price_async(symbol: str) -> Optional[dict]:
    """Async wrapper around sync fetch_price using a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, fetch_price, symbol)


async def fetch_all_prices(symbols: list) -> list:
    """
    Fetch multiple assets concurrently. 
    Up to 5 assets at once using ThreadPoolExecutor.
    Returns list of results (dict or None for failures).
    """
    tasks = [fetch_price_async(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed = []
    for sym, result in zip(symbols, results):
        if isinstance(result, Exception):
            logger.error(f"[{__name__}] Async fetch failed for {sym}: {result}")
            processed.append(None)
        else:
            processed.append(result)
    
    return processed

