from config.constants import RISK_MULTIPLIERS
from storage import models
from utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_india_trade_risk(commodity_query: str) -> dict:
    """
    Evaluates India's import dependency for a given sector/commodity type.
    We proxy Fuel/Metals using World Bank Trade Flows % logic mapped previously.
    """
    try:
        # We query the latest trade flow record for India as reporter
        record = models.TradeFlows.select().where(
            (models.TradeFlows.reporter_country == "India") &
            (models.TradeFlows.commodity.contains(commodity_query)) &
            (models.TradeFlows.trade_type == "import")
        ).order_by(models.TradeFlows.year.desc()).first()
        
        if not record or not record.quantity:
            return {"dependency_pct": 0.0, "risk_score": 0, "status": "Unknown"}
            
        dep_pct = record.quantity
        risk = 0
        status = "Low Alert"
        
        if dep_pct > 20.0:
            risk = RISK_MULTIPLIERS.get("india_import_share_high", 20)
            status = "High Vulnerability (>20% Import Share)"
        elif dep_pct > 10.0:
            risk = int(RISK_MULTIPLIERS.get("india_import_share_high", 20) / 2)
            status = "Moderate Vulnerability"
            
        return {
            "commodity": record.commodity,
            "dependency_pct": round(dep_pct, 2),
            "risk_score": risk,
            "status": status,
            "year_referenced": record.year
        }
        
    except Exception as e:
        logger.error(f"[{__name__}] Failed to evaluate India trade risk: {e}")
        return {"dependency_pct": 0.0, "risk_score": 0, "status": "Error"}
