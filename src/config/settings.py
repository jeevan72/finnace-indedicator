import os
from pathlib import Path
from dotenv import load_dotenv

# Load all potential environment variables.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure necessary directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
EIA_API_KEY = os.getenv("EIA_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GNEWS_KEY = os.getenv("GNEWS_KEY", "")
OPEN_EXCHANGE_RATES_KEY = os.getenv("OPEN_EXCHANGE_RATES_KEY", "")
COMTRADE_API_KEY = os.getenv("COMTRADE_API_KEY", "")

# Database Config
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "terminal.db"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "terminal.log"))

# Application Configuration
CACHE_TTL_PRICES = int(os.getenv("CACHE_TTL_PRICES", 60))
CACHE_TTL_OPTIONS = int(os.getenv("CACHE_TTL_OPTIONS", 300))
CACHE_TTL_MACRO = int(os.getenv("CACHE_TTL_MACRO", 3600))
MARKET_TIMEZONE = os.getenv("MARKET_TIMEZONE", "Asia/Kolkata")
