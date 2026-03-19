import time
from datetime import datetime, timedelta
from config.constants import RISK_MULTIPLIERS
from storage import models
from utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_supply_score(commodity: str) -> dict:
    """
    Computes an aggregate supply risk score (0-100) for a given commodity (e.g. 'Crude Oil')
    Validates bullish/bearish signs over the last 30 days.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        events = models.SupplyEvents.select().where(
            (models.SupplyEvents.commodity == commodity) &
            (models.SupplyEvents.timestamp >= thirty_days_ago)
        ).order_by(models.SupplyEvents.timestamp.desc())
        
        score = 0
        factors = []
        for ev in events:
            if ev.signal == "bullish":
                # A bullish supply event implies supply constraint (risk goes up)
                val = RISK_MULTIPLIERS.get("risk_level_high", 25)
                score += val
                factors.append(f"Constraint: {ev.event_type} ({ev.value} {ev.unit}) [+ {val}]")
            elif ev.signal == "bearish":
                # A bearish supply event implies surplus (risk goes down)
                val = RISK_MULTIPLIERS.get("risk_level_medium", 15)
                score -= val
                factors.append(f"Surplus: {ev.event_type} ({ev.value} {ev.unit}) [- {val}]")
                
        # Base score 50 (neutral). Normalize to 0-100
        final_score = max(0, min(100, 50 + score))
        
        return {
            "commodity": commodity,
            "supply_risk_score": final_score,
            "factors": factors[:5] # Top 5 most recent drivers
        }
    except Exception as e:
        logger.error(f"[{__name__}] Failed to evaluate supply score for {commodity}: {e}")
        return {"commodity": commodity, "supply_risk_score": 50, "factors": ["Calculation error"]}
