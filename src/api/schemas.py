"""
Pydantic response schemas for the FastAPI endpoints.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PriceResponse(BaseModel):
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: Optional[float] = None
    timestamp: str
    source: str
    is_delayed: bool = False
    currency: str = "INR"


class OptionsResponse(BaseModel):
    symbol: str
    expiry: str
    pcr: Optional[float] = None
    max_pain: Optional[float] = None
    iv_rank: Optional[float] = None
    atm_iv: Optional[float] = None
    timestamp: str


class EventResponse(BaseModel):
    symbol: str
    event_type: str
    headline: str
    keywords_matched: Optional[str] = None
    timestamp: str


class SanctionResponse(BaseModel):
    entity_name: str
    country: Optional[str] = None
    asset_type: Optional[str] = None
    list_type: Optional[str] = None
    added_date: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    prices_count: int
    last_update: Optional[str] = None
