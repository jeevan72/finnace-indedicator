from datetime import datetime
import math

class ValidationError(Exception):
    """Raised when an API response violates the strict schema output contract."""
    pass

def _check_keys(data: dict, required_keys: list):
    for key in required_keys:
        if key not in data:
            raise ValidationError(f"Missing required key: '{key}'")

def _check_float_not_nan(val: float, field_name: str):
    if not isinstance(val, (int, float)):
        raise ValidationError(f"Field '{field_name}' must be numeric, got {type(val)}")
    if math.isnan(val):
        raise ValidationError(f"Field '{field_name}' cannot be NaN")

def validate_price_record(data: dict) -> dict:
    required = ["symbol", "name", "price", "change_pct", "volume", "timestamp", "source", "is_delayed"]
    _check_keys(data, required)
    
    _check_float_not_nan(data["price"], "price")
    if data["price"] <= 0:
        raise ValidationError(f"Price must be strictly positive, got {data['price']}")
        
    _check_float_not_nan(data["change_pct"], "change_pct")
    
    if data["volume"] is not None and not isinstance(data["volume"], int):
        # coerce to int if possible
        try:
            data["volume"] = int(float(data["volume"]))
        except (ValueError, TypeError):
             raise ValidationError(f"Volume must be integer or None")
             
    try:
        # Just verifying parseability
        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        raise ValidationError(f"Invalid timestamp format: {data['timestamp']}")
        
    if not isinstance(data["is_delayed"], bool):
        raise ValidationError("is_delayed must be boolean")
    
    # Default currency to INR if not provided
    if "currency" not in data:
        data["currency"] = "INR"
        
    return data

def validate_supply_event(data: dict) -> dict:
    required = ["commodity", "event_type", "value", "unit", "signal", "timestamp", "source"]
    _check_keys(data, required)
    
    _check_float_not_nan(data["value"], "value")
    if data["signal"] not in ("bullish", "bearish", "neutral"):
        raise ValidationError(f"Invalid signal type: {data['signal']}")
        
    return data

def validate_options_snapshot(data: dict) -> dict:
    required = ["symbol", "expiry", "pcr", "max_pain", "iv_rank", "atm_iv", "timestamp"]
    _check_keys(data, required)
    
    _check_float_not_nan(data["pcr"], "pcr")
    _check_float_not_nan(data["max_pain"], "max_pain")
    _check_float_not_nan(data["iv_rank"], "iv_rank")
    _check_float_not_nan(data["atm_iv"], "atm_iv")
    
    if not (0 <= data["iv_rank"] <= 100):
        # We cap it at 0 to 100 due to data spikes
        data["iv_rank"] = max(0, min(100, data["iv_rank"]))
        
    return data

def validate_macro_series(data: dict) -> dict:
    required = ["indicator_code", "indicator_name", "country", "value", "period", "timestamp", "source"]
    _check_keys(data, required)
    
    _check_float_not_nan(data["value"], "value")
    
    return data
