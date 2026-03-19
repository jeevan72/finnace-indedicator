# Rate limit dictionary for fetcher config use
# Stored as (calls_allowed, period_in_seconds)
RATE_LIMITS = {
    "yahoo_finance": (2000, 3600),   # ~2000 per hr
    "alpha_vantage": (25, 86400),    # 25 per day total
    "fred": (120, 60),               # 120 req per min
    "eia": (5, 1),                   # 5 req per sec
    "nse_india": (30, 60),           # ~30 req per min
    "sec_edgar": (10, 1),            # 10 req per sec
    "newsapi": (100, 86400),         # 100 req per day
    "gnews": (100, 86400),           # 100 req per day
    "coingecko": (30, 60),           # 30 req per min
    "open_exchange_rates": (1000, 2592000) # 1000 req per month
}
