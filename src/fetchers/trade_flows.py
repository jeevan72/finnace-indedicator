import time
import pandas as pd
from typing import List

import world_bank_data as wb

from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from utils.time_utils import utc_now
from storage import models

logger = get_logger(__name__)

@rate_limit("worldbank")
@retry(max_attempts=3, backoff_factor=2)
def _fetch_imports(indicator: str) -> pd.Series:
    """ Pulls Indian trade dependency % for fuel/ores from World Bank """
    # TX.VAL.MRCH.OR.ZS = Ores and metals exports (% of merchandise exports) -> Just a proxy if real imports API isn't easy
    # TM.VAL.FUEL.ZS.UN = Fuel imports (% of merchandise imports)
    return wb.get_series(indicator, country='IND')

def fetch_india_trade_flows() -> List[dict]:
    """
    Tracks strategic trade dependency metrics:
    e.g., India's fuel import dependency as a %.
    """
    results = []
    indicators = [
        ("TM.VAL.FUEL.ZS.UN", "Fuel Imports", "import"),
        ("TM.VAL.MMTL.ZS.UN", "Ores and Metals Imports", "import") # Proxy indicator
    ]
    
    for ind, commodity, t_type in indicators:
        try:
            series = _fetch_imports(ind)
            series = series.dropna()
            if series.empty:
                continue
                
            last_idx = series.index[-1]
            last_year = last_idx[2] if len(last_idx) > 2 else last_idx[1] if len(last_idx) > 1 else last_idx
            last_val = series.iloc[-1]
            
            raw = {
                "commodity": commodity,
                "reporter_country": "India",
                "partner_country": "World",
                "trade_type": t_type,
                "value_usd": None, # Storing relative % quantity instead
                "quantity": float(last_val), 
                "unit": "% of Total Imports",
                "year": int(last_year),
                "source": "World Bank"
            }
            
            # Upsert
            exists = models.TradeFlows.select().where(
                (models.TradeFlows.commodity == commodity) &
                (models.TradeFlows.year == raw["year"])
            ).exists()
            
            if not exists:
                models.TradeFlows.create(**raw)
                
            results.append(raw)
            
        except Exception as e:
            logger.error(f"[{__name__}] Failed to fetch trade flows for {commodity}: {e}")
            res = _fallback_from_db("India", commodity)
            if res: results.append(res)
            
    return results

def _fallback_from_db(country: str, commodity: str) -> dict:
    try:
        record = models.TradeFlows.select().where(
            (models.TradeFlows.reporter_country == country) &
            (models.TradeFlows.commodity == commodity)
        ).order_by(models.TradeFlows.year.desc()).first()
        
        if record:
            return {
                "commodity": record.commodity,
                "reporter_country": record.reporter_country,
                "partner_country": record.partner_country,
                "trade_type": record.trade_type,
                "quantity": record.quantity,
                "unit": record.unit,
                "year": record.year,
                "source": record.source,
                "stale": True
            }
        return {}
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback failed for Trade Flows: {e}")
        return {}
