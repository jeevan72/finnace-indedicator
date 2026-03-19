def safe_float(value, default=None):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=None):
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def truncate_string(val: str, max_len: int) -> str:
    """Safely truncates string, useful for UI rendering or headline DB limits."""
    if not val:
        return val
    return val[:max_len] + "..." if len(val) > max_len else val
