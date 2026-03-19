"""
FastAPI REST API server for the Financial Intelligence Terminal.
Provides REST endpoints and WebSocket for real-time price updates.
"""
import sys
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

# Resolve src path
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC_DIR))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from storage.db import init_db
from storage import models
from fetchers.prices import fetch_price, fetch_all_prices
from config.assets import METALS, ENERGY, INDICES, FOREX, VOLATILITY
from api.schemas import PriceResponse, OptionsResponse, EventResponse, SanctionResponse, HealthResponse


# ── Active WebSocket connections ──
connected_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title="Financial Intelligence Terminal API",
    description="REST + WebSocket API for commodity, equity, and macro data",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────── Helper ──────────────────
def _get_latest_prices(category: Optional[str] = None) -> list[dict]:
    """Query latest prices from DB, optionally filtered by category."""
    records = models.Prices.select().order_by(models.Prices.timestamp.desc())
    latest = {}
    for r in records:
        if r.symbol not in latest:
            latest[r.symbol] = r

    if category:
        category_map = {
            "metals": METALS,
            "energy": ENERGY,
            "indices": INDICES,
            "forex": FOREX,
            "volatility": VOLATILITY,
        }
        allowed = set(category_map.get(category.lower(), []))
        latest = {k: v for k, v in latest.items() if k in allowed}

    return [
        {
            "symbol": r.symbol,
            "name": r.name,
            "price": r.price,
            "change_pct": r.change_pct,
            "volume": r.volume,
            "timestamp": r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
            "source": r.source,
            "is_delayed": r.is_delayed,
            "currency": getattr(r, "currency", "INR"),
        }
        for r in latest.values()
    ]


# ────────────────── REST Endpoints ──────────────────


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    count = models.Prices.select().count()
    last = models.Prices.select().order_by(models.Prices.timestamp.desc()).first()
    return HealthResponse(
        status="ok",
        db_connected=True,
        prices_count=count,
        last_update=last.timestamp.isoformat() if last else None,
    )


@app.get("/api/prices", response_model=list[PriceResponse])
def get_prices(category: Optional[str] = Query(None, description="Filter: metals, energy, indices, forex, volatility")):
    """Get latest prices, optionally filtered by category."""
    return _get_latest_prices(category)


@app.get("/api/prices/{symbol}", response_model=PriceResponse)
def get_price_detail(symbol: str):
    """Get latest price for a specific symbol."""
    r = models.Prices.select().where(models.Prices.symbol == symbol).order_by(models.Prices.timestamp.desc()).first()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    return PriceResponse(
        symbol=r.symbol, name=r.name, price=r.price, change_pct=r.change_pct,
        volume=r.volume,
        timestamp=r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
        source=r.source, is_delayed=r.is_delayed, currency=getattr(r, "currency", "INR"),
    )


@app.post("/api/fetch/{symbol}")
async def trigger_fetch(symbol: str):
    """Trigger an immediate fetch for a symbol."""
    result = await asyncio.get_event_loop().run_in_executor(None, fetch_price, symbol)
    if result:
        return {"status": "ok", "data": result}
    return {"status": "error", "message": f"Failed to fetch {symbol}"}


@app.post("/api/fetch-all")
async def trigger_fetch_all():
    """Trigger an immediate fetch for all commodity assets."""
    symbols = METALS + ENERGY
    results = await fetch_all_prices(symbols)
    success = sum(1 for r in results if r is not None)
    return {"status": "ok", "fetched": success, "total": len(symbols)}


@app.get("/api/options", response_model=list[OptionsResponse])
def get_options():
    """Get latest options snapshots."""
    opts = models.OptionsSnapshot.select().order_by(models.OptionsSnapshot.timestamp.desc())
    latest = {}
    for o in opts:
        if o.symbol not in latest:
            latest[o.symbol] = o
    return [
        OptionsResponse(
            symbol=o.symbol, expiry=str(o.expiry), pcr=o.pcr, max_pain=o.max_pain,
            iv_rank=o.iv_rank, atm_iv=o.atm_iv,
            timestamp=o.timestamp.isoformat() if hasattr(o.timestamp, "isoformat") else str(o.timestamp),
        )
        for o in latest.values()
    ]


@app.get("/api/events", response_model=list[EventResponse])
def get_events(limit: int = Query(20, ge=1, le=100)):
    """Get recent BSE events."""
    events = models.Events.select().order_by(models.Events.timestamp.desc()).limit(limit)
    return [
        EventResponse(
            symbol=e.symbol, event_type=e.event_type, headline=e.headline,
            keywords_matched=e.keywords_matched,
            timestamp=e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp),
        )
        for e in events
    ]


@app.get("/api/sanctions", response_model=list[SanctionResponse])
def get_sanctions(limit: int = Query(20, ge=1, le=100)):
    """Get tracked sanctions entities."""
    sanctions = models.SanctionsWatch.select().order_by(models.SanctionsWatch.id.desc()).limit(limit)
    return [
        SanctionResponse(
            entity_name=s.entity_name, country=s.country, asset_type=s.asset_type,
            list_type=s.list_type, added_date=str(s.added_date) if s.added_date else None,
        )
        for s in sanctions
    ]


# ────────────────── WebSocket ──────────────────


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for real-time price updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Send latest prices every 30 seconds
            prices = _get_latest_prices()
            await websocket.send_json(prices)
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
