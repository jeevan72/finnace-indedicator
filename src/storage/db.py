from peewee import SqliteDatabase
from config.settings import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize database but do not connect yet, let app control lifecycle
db = SqliteDatabase(DB_PATH)

def init_db():
    from storage.models import (
        Prices, DailyEOD, FO_OI, OptionsSnapshot, Events, 
        TradeFlows, MacroSeries, HedgingFlags, SupplyEvents, SanctionsWatch
    )
    try:
        db.connect()
        db.create_tables([
            Prices, DailyEOD, FO_OI, OptionsSnapshot, Events,
            TradeFlows, MacroSeries, HedgingFlags, SupplyEvents, SanctionsWatch
        ], safe=True)
        logger.info(f"Database successfully initialized at {DB_PATH}")
    except Exception as e:
        logger.critical(f"Failed to initialize SQLite database: {e}", exc_info=True)
    finally:
        if not db.is_closed():
            db.close()

def get_db():
    return db
