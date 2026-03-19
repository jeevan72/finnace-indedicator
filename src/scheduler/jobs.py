import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from utils.logger import get_logger
from fetchers.prices import fetch_price
from fetchers.nse_bhavcopy import fetch_and_store_bhavcopy
from fetchers.options_chain import fetch_options_chain
from fetchers.eia_supply import fetch_eia_crude_inventory
from fetchers.macro import fetch_macro_indicators
from fetchers.bse_announcements import fetch_bse_announcements
from fetchers.trade_flows import fetch_india_trade_flows
from fetchers.sanctions import scan_sanctions_watch
from config.assets import YF_TICKERS

logger = get_logger(__name__)

def job_fetch_commodity_prices():
    """Fetches high-frequency commodity indicators."""
    logger.info("=== Running Scheduled Job: Commodity Prices ===")
    for name in ["Gold", "Silver", "WTI Crude", "Brent Crude"]:
        fetch_price(name)
        time.sleep(1) # Safe spacing
        
def job_fetch_indices_prices():
    """Fetches lower-frequency index indicators."""
    logger.info("=== Running Scheduled Job: Indices & FX ===")
    for name in ["S&P 500", "Nifty 50", "India VIX", "USD/INR", "DXY"]:
        fetch_price(name)
        time.sleep(1)

def job_fetch_nse_derivatives():
    """Fetches NSE Bhavcopy and Options Chains."""
    logger.info("=== Running Scheduled Job: NSE Updates ===")
    fetch_and_store_bhavcopy()
    fetch_options_chain("NIFTY")
    fetch_options_chain("BANKNIFTY")

def job_fetch_macro_supply_geopolitics():
    """Fetches macro info, EIA supply, trade flows, and sanctions weekly/daily."""
    logger.info("=== Running Scheduled Job: Macro & Supply ===")
    try:
        fetch_eia_crude_inventory()
    except Exception as e:
        logger.error(e)
        
    try:
        fetch_macro_indicators()
    except Exception as e:
        logger.error(e)
        
    try:
        fetch_india_trade_flows()
    except Exception as e:
        logger.error(e)
        
    try:
        scan_sanctions_watch()
    except Exception as e:
        logger.error(e)

def job_fetch_bse_announcements():
    """Scans BSE for tracked events."""
    logger.info("=== Running Scheduled Job: BSE Announcements ===")
    # 500325 is Reliance Industries scrip code as an example
    fetch_bse_announcements("RELIANCE", "500325") 

def start_scheduler():
    logger.info("Initializing APScheduler Background Engine...")
    scheduler = BlockingScheduler()

    # Intraday
    scheduler.add_job(job_fetch_commodity_prices, IntervalTrigger(minutes=15), id="commodity_prices")
    scheduler.add_job(job_fetch_indices_prices, IntervalTrigger(minutes=30), id="indices_prices")
    scheduler.add_job(job_fetch_bse_announcements, IntervalTrigger(minutes=60), id="bse_announcements")
    
    # End of Day
    # NSE Bhavcopy released around 18:00 IST (12:30 UTC)
    scheduler.add_job(job_fetch_nse_derivatives, CronTrigger(hour=13, minute=0, timezone="UTC"), id="nse_eod")
    
    # Weekly/Daily Macro
    scheduler.add_job(job_fetch_macro_supply_geopolitics, CronTrigger(hour=1, minute=0, timezone="UTC"), id="macro_daily")

    logger.info("Scheduler Started. Press Ctrl+C to exit.")
    scheduler.start()
