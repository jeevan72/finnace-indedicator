import pandas as pd
import numpy as np
from storage import models
from utils.logger import get_logger

logger = get_logger(__name__)

def compute_volatility_percentile(symbol: str, window: int = 20) -> float:
    """
    Calculates the current rolling volatility percentile (0-100) for a given symbol.
    Queries the DailyEOD prices from Peewee SQLite.
    """
    try:
        # Fetch last 252 trading days (~1 year)
        records = models.DailyEOD.select(models.DailyEOD.close, models.DailyEOD.date).where(
            models.DailyEOD.symbol == symbol
        ).order_by(models.DailyEOD.date.desc()).limit(252)
        
        df = pd.DataFrame(list(records.dicts()))
        if len(df) < window + 1:
            logger.debug(f"[{__name__}] Not enough EOD data for {symbol} ({len(df)} rows). Defaulting to 50.0")
            return 50.0
            
        df = df.sort_values(by="date", ascending=True)
        # Daily log returns
        df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
        
        # Annualized rolling volatility
        df["rolling_vol"] = df["log_ret"].rolling(window=window).std() * np.sqrt(252)
        
        vols = df["rolling_vol"].dropna().values
        if len(vols) == 0:
            return 50.0
            
        current_vol = vols[-1]
        
        # Empirical percentile rank
        percentile = (np.sum(vols <= current_vol) / len(vols)) * 100
        return round(percentile, 2)
        
    except Exception as e:
        logger.error(f"[{__name__}] Failed to compute volatility percentile for {symbol}: {e}", exc_info=True)
        return 50.0
