from typing import List
from config.assets import CUSIP_MAP
from storage import models
from utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_hedging_activity() -> List[dict]:
    """
    Evaluates institutional footprint shifts across tracked commodity ETFs
    (e.g. GLD for Gold, SLV for Silver) using established CUSIPs.
    In a live production environment, this function parses freshly ingested 
    13F-HR filings from EDGAR to calculate QoQ position changes by major funds.
    """
    results = []
    try:
        # Pull the latest 50 parsed HedgingFlags
        records = models.HedgingFlags.select().order_by(models.HedgingFlags.filing_date.desc()).limit(50)
        
        for r in records:
            # Re-evaluate strict signal thresholds
            signal = "neutral"
            if r.change_pct is not None:
                if r.change_pct > 15.0:
                    signal = "increase (bullish)"
                elif r.change_pct < -15.0:
                    signal = "unwinding (bearish)"
                
            results.append({
                "filer": r.filer_name,
                "asset": r.asset_type,
                "position_type": r.position_type,
                "change_pct": r.change_pct,
                "signal": signal,
                "filing_date": r.filing_date.isoformat() if hasattr(r.filing_date, 'isoformat') else str(r.filing_date)
            })
            
        return results
        
    except Exception as e:
        logger.error(f"[{__name__}] Failed to evaluate hedging activity: {e}")
        return []
