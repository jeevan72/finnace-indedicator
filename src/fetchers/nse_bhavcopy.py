import io
import time
import pandas as pd
from datetime import timedelta
from typing import List, Optional

from utils.nse_session import NSESessionManager
from utils.logger import get_logger
from utils.retry import retry
from utils.time_utils import utc_now
from utils.validators import validate_daily_eod
from storage import models
from config.settings import MARKET_TIMEZONE
from zoneinfo import ZoneInfo

logger = get_logger(__name__)

@retry(max_attempts=3, backoff_factor=2)
def _download_bhavcopy(date_str: str) -> Optional[pd.DataFrame]:
    """
    Downloads the full sec_bhavdata_full file from NSE.
    Includes Delivery Quantities and Percentages.
    """
    url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{date_str}.csv"
    try:
        resp = NSESessionManager.fetch(url)
        # Load CSV into pandas
        df = pd.read_csv(io.StringIO(resp.text))
        # Strip whitespace from column names just in case
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        logger.warning(f"[{__name__}] Failed to download Bhavcopy for {date_str}. It might be a holiday/weekend: {e}")
        return None

def fetch_and_store_bhavcopy() -> int:
    """
    Walks backwards from today to find the most recent trading day's bhavcopy.
    Parses and stores it in the DailyEOD table. Returns number of records inserted.
    """
    # Start with today in IST
    current_date = utc_now().astimezone(ZoneInfo(MARKET_TIMEZONE))
    
    df = None
    target_date = current_date
    
    # Try up to 7 days back to handle long holiday weekends
    for _ in range(7):
        date_str = target_date.strftime("%d%m%Y")
        
        # Check if already in DB to avoid redundant parsing
        iso_dt = target_date.strftime("%Y-%m-%d")
        exists = models.DailyEOD.select().where(models.DailyEOD.date == iso_dt).exists()
        if exists:
            logger.info(f"[{__name__}] Bhavcopy for {iso_dt} already exists in DB. Skipping.")
            return 0
            
        df = _download_bhavcopy(date_str)
        if df is not None:
            break
            
        target_date -= timedelta(days=1)
        
    if df is None:
        logger.error(f"[{__name__}] Could not retrieve any Bhavcopy for the past 7 days.")
        return 0

    iso_dt = target_date.strftime("%Y-%m-%d")
    logger.info(f"[{__name__}] Successfully downloaded Bhavcopy for {iso_dt}. Processing...")
    
    # Filter only for EQ (Equity) series to drop bonds, etc.
    if "SERIES" in df.columns:
        df = df[df["SERIES"].str.strip() == "EQ"]
        
    records_to_insert = []
    
    for _, row in df.iterrows():
        try:
            symbol = str(row.get("SYMBOL", "")).strip()
            if not symbol:
                continue
                
            vol = row.get("TTL_TRD_QNTY", 0)
            deliv_qty = row.get("DELIV_QTY", 0)
            deliv_pct = row.get("DELIV_PER", 0.0)
            
            # Handle '-' strings from NSE indicating 0
            if isinstance(deliv_qty, str) and deliv_qty.strip() == "-": deliv_qty = 0
            if isinstance(deliv_pct, str) and deliv_pct.strip() == "-": deliv_pct = 0.0
            
            raw_record = {
                "symbol": symbol,
                "date": iso_dt,
                "open_price": float(row.get("OPEN_PRICE", 0.0)),
                "high_price": float(row.get("HIGH_PRICE", 0.0)),
                "low_price": float(row.get("LOW_PRICE", 0.0)),
                "close_price": float(row.get("CLOSE_PRICE", 0.0)),
                "volume": int(vol),
                "delivery_qty": int(deliv_qty),
                "delivery_pct": float(deliv_pct)
            }
            
            # Use strict schema validator
            validated = validate_daily_eod(raw_record)
            
            # Mapping matching Peewee model
            records_to_insert.append(models.DailyEOD(
                symbol=validated["symbol"],
                date=validated["date"],
                open_price=validated["open_price"],
                high_price=validated["high_price"],
                low_price=validated["low_price"],
                close_price=validated["close_price"],
                volume=validated["volume"],
                delivery_qty=validated["delivery_qty"],
                delivery_pct=validated["delivery_pct"]
            ))
        except Exception as e:
            # Skip corrupted rows individually
            logger.debug(f"[{__name__}] Skipped row in bhavcopy due to parse error: {e}")
            continue

    # Bulk insert for performance (SQLite limit is 999 variables, batch by 100)
    if records_to_insert:
        with models.db.atomic():
            models.DailyEOD.bulk_create(records_to_insert, batch_size=100)
        logger.info(f"[{__name__}] Inserted {len(records_to_insert)} EOD records for {iso_dt}.")
    
    return len(records_to_insert)
