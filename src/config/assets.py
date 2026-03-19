# Core Watchlist Arrays
METALS = ["Gold", "Silver", "Copper", "Nickel", "Lithium", "Cobalt"]
ENERGY = ["WTI Crude", "Brent Crude", "Natural Gas", "Coal"]
INDICES = ["Nifty", "Sensex", "S&P 500", "NASDAQ", "DAX", "FTSE", "Nikkei"]
FOREX = ["USD/INR", "DXY", "EUR/USD", "CNY/USD"]
VOLATILITY = ["India VIX", "CBOE VIX", "OVX", "GVZ"]

# Ticker mapping for Yahoo Finance
YF_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Copper": "HG=F",
    "Nickel": "ALI=F",
    "WTI Crude": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Coal": "MTF=F",  # API-specific Rotterdam coal or similar
    "Nifty": "^NSEI",
    "Sensex": "^BSESN",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "FTSE": "^FTSE",
    "Nikkei": "^N225",
    "USD/INR": "INR=X",
    "DXY": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "CNY/USD": "CNYUSD=X",
    "CBOE VIX": "^VIX",
    "India VIX": "^INDIAVIX",
    "OVX": "^OVX",  # Crude Oil volatility
    "GVZ": "^GVZ"   # Gold volatility
}

# Static Delay mappings
IS_DELAYED_MONTHLY = ["Lithium", "Cobalt"]

# CUSIP SEC Mapping
CUSIP_MAP = {
    "912810": "US Treasury / Rates",
    "37816W103": "GLD", # SPDR Gold CUSIP (Example)
    "91232N108": "USO", # US Oil Fund CUSIP (Example)
    "46428Q109": "SLV"  # iShares Silver Trust (Example)
}
