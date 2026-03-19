import asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from utils.logger import get_logger
from fetchers.prices import fetch_price, fetch_all_prices
from fetchers.nse_bhavcopy import fetch_and_store_bhavcopy
from fetchers.options_chain import fetch_options_chain
from fetchers.eia_supply import fetch_eia_crude_inventory
from fetchers.macro import fetch_macro_indicators
from fetchers.bse_announcements import fetch_bse_announcements
from fetchers.trade_flows import fetch_india_trade_flows
from fetchers.sanctions import scan_sanctions_watch

logger = get_logger(__name__)

def job_fetch_commodity_prices():
    """Fetches high-frequency commodity indicators — CONCURRENTLY."""
    logger.info("=== Running Scheduled Job: Commodity Prices (async) ===")
    symbols = ["Gold", "Silver", "WTI Crude", "Brent Crude", "Copper", "Nickel", "Natural Gas", "Coal"]
    results = asyncio.run(fetch_all_prices(symbols))
    success = sum(1 for r in results if r is not None)
    logger.info(f"=== Commodity Prices: {success}/{len(symbols)} fetched ===")
        
def job_fetch_indices_prices():
    """Fetches lower-frequency index indicators — CONCURRENTLY."""
    logger.info("=== Running Scheduled Job: Indices & FX (async) ===")
    symbols = ["S&P 500", "Nifty", "Sensex", "India VIX", "CBOE VIX", "USD/INR", "DXY", "NASDAQ"]
    results = asyncio.run(fetch_all_prices(symbols))
    success = sum(1 for r in results if r is not None)
    logger.info(f"=== Indices & FX: {success}/{len(symbols)} fetched ===")

def job_fetch_nse_derivatives():
    """Fetches NSE Bhavcopy and Options Chains."""
    logger.info("=== Running Scheduled Job: NSE Updates ===")
    fetch_and_store_bhavcopy()
    fetch_options_chain("NIFTY")
    fetch_options_chain("BANKNIFTY")

def job_fetch_macro_supply_geopolitics():
    """Fetches macro info, EIA supply, trade flows, and sanctions weekly/daily."""
    logger.info("=== Running Scheduled Job: Macro & Supply ===")
    for fn in [fetch_eia_crude_inventory, fetch_macro_indicators, fetch_india_trade_flows, scan_sanctions_watch]:
        try:
            fn()
        except Exception as e:
            logger.error(f"[{fn.__name__}] {e}")

def job_fetch_bse_announcements():
    """Scans BSE for tracked events."""
    logger.info("=== Running Scheduled Job: BSE Announcements ===")
    fetch_bse_announcements("RELIANCE", "500325") 

def start_scheduler():
    logger.info("Initializing APScheduler Background Engine...")
    scheduler = BlockingScheduler()

    # Intraday — concurrent batch fetching
    scheduler.add_job(job_fetch_commodity_prices, IntervalTrigger(minutes=15), id="commodity_prices")
    scheduler.add_job(job_fetch_indices_prices, IntervalTrigger(minutes=30), id="indices_prices")
    scheduler.add_job(job_fetch_bse_announcements, IntervalTrigger(minutes=60), id="bse_announcements")
    
    # End of Day — NSE Bhavcopy released around 18:00 IST (12:30 UTC)
    scheduler.add_job(job_fetch_nse_derivatives, CronTrigger(hour=13, minute=0, timezone="UTC"), id="nse_eod")
    
    # Weekly/Daily Macro
    scheduler.add_job(job_fetch_macro_supply_geopolitics, CronTrigger(hour=1, minute=0, timezone="UTC"), id="macro_daily")

    logger.info("Scheduler Started. Press Ctrl+C to exit.")
    scheduler.start()
