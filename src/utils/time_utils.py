from datetime import datetime
from zoneinfo import ZoneInfo
from config.settings import MARKET_TIMEZONE

def utc_now() -> datetime:
    """Returns naive UTC datetime object as dictated by schema guidelines."""
    return datetime.utcnow()

def to_ist(naive_utc_time) -> datetime:
    """Converts a naive UTC datetime from the database into IST."""
    if isinstance(naive_utc_time, str):
        try:
            naive_utc_time = datetime.fromisoformat(naive_utc_time.replace('Z', '+00:00')[:26])
        except ValueError:
            # Fallback if format is different
            pass
    # First inject the UTC timezone since DB provides naive UTC datetime
    if not hasattr(naive_utc_time, "replace"):
        raise TypeError(f"Expected datetime, got {type(naive_utc_time)}")
    utc_aware = naive_utc_time.replace(tzinfo=ZoneInfo("UTC"))
    return utc_aware.astimezone(ZoneInfo(MARKET_TIMEZONE))

def format_ist_display(naive_utc_time: datetime) -> str:
    """Formats naive UTC timestamp to '17 Mar 2025, 14:30 IST' display format."""
    ist_time = to_ist(naive_utc_time)
    return ist_time.strftime("%d %b %Y, %H:%M IST")
