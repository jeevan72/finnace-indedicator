import pandas as pd
import numpy as np

def compute_pcr(options_data: list) -> float:
    """ Computes the Put-Call Ratio by Total Open Interest. """
    total_ce_oi = sum([opt.get("CE", {}).get("openInterest", 0) for opt in options_data])
    total_pe_oi = sum([opt.get("PE", {}).get("openInterest", 0) for opt in options_data])
    
    if total_ce_oi == 0:
        return 0.0
    return round(total_pe_oi / total_ce_oi, 4)

def compute_max_pain(options_data: list) -> float:
    """ 
    Computes Max Pain strike based on options chain data.
    Max Pain is the strike where option buyers lose the most money (minimum intrinsic value).
    """
    strikes = sorted(list(set([opt.get("strikePrice") for opt in options_data if opt.get("strikePrice")])))
    if not strikes:
        return 0.0
        
    pain_values = {}
    for test_strike in strikes:
        total_pain = 0
        for opt in options_data:
            strike = opt.get("strikePrice", 0)
            ce_oi = opt.get("CE", {}).get("openInterest", 0) * 50 # Nifty lot size approx, relative size works too
            pe_oi = opt.get("PE", {}).get("openInterest", 0) * 50
            
            # CE pain (if market expires at test_strike, calls with strike < test_strike have value)
            if test_strike > strike:
                total_pain += (test_strike - strike) * ce_oi
                
            # PE pain (if market expires at test_strike, puts with strike > test_strike have value)
            if test_strike < strike:
                total_pain += (strike - test_strike) * pe_oi
                
        pain_values[test_strike] = total_pain
        
    return min(pain_values, key=pain_values.get)

def extract_atm_iv(options_data: list, underlying_value: float) -> float:
    """ Returns the average IV of CE and PE at the strike closest to ATM. """
    if not underlying_value or not options_data:
        return 0.0
        
    strikes = [opt.get("strikePrice") for opt in options_data if opt.get("strikePrice")]
    if not strikes:
        return 0.0
        
    atm_strike = min(strikes, key=lambda x: abs(x - underlying_value))
    
    # Find the record for ATM strike
    for opt in options_data:
        if opt.get("strikePrice") == atm_strike:
            ce_iv = opt.get("CE", {}).get("impliedVolatility", 0)
            pe_iv = opt.get("PE", {}).get("impliedVolatility", 0)
            return round((ce_iv + pe_iv) / 2.0, 4)
            
    return 0.0

def compute_iv_rank(current_iv: float, iv_history: list) -> float:
    """
    Computes IV Rank (0-100)
    Formula: (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) * 100
    """
    if not iv_history or len(iv_history) < 2:
        return 50.0  # Safe neutral default if history missing
        
    iv_low = min(iv_history)
    iv_high = max(iv_history)
    
    if iv_high == iv_low:
        return 50.0
        
    rank = ((current_iv - iv_low) / (iv_high - iv_low)) * 100
    return round(max(0.0, min(100.0, rank)), 2)
