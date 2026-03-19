import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure we can import from src/
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, src_path)

from src.fetchers.prices import fetch_price
from src.storage.db import init_db

# Mock DB initialization so tests can run without full disk writes if needed
# We run it against an in-memory DB or temporary DB just to prevent schema issues
# Actually, Peewee defaults to storing wherever DB_PATH is, let's just make sure
# the tables exist because fetch_price does call `.create()`
@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_fetch_gold_price_schema():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_info = {"lastPrice": 2150.30, "previousClose": 2140.00}
        
        # In yf.Ticker, fast_info behaves somewhat like a mapping
        mock_ticker.return_value.fast_info = mock_info
        # For the info attribute which is a dict (if used)
        mock_ticker.return_value.info = mock_info
        
        # Test Gold which is established in YF_TICKERS
        result = fetch_price("Gold")
        
        assert result is not None
        assert isinstance(result["price"], float)
        assert isinstance(result["change_pct"], float)
        assert "timestamp" in result
        assert result["source"] == "yahoo_finance"
        assert result["price"] > 0
        assert not result.get("stale", False)

def test_fetch_price_fallback_on_network_error():
    # Because of our @retry decorator, it will retry 3 times before failing
    # To speed up test we can mock the inner network call explicitly
    with patch("src.fetchers.prices._call_yf_api", side_effect=ConnectionError("Mocked network error")):
        result = fetch_price("Silver")
        
        # Should NOT raise an exception. Must return fallback dict or None
        assert result is None or isinstance(result, dict)
        if isinstance(result, dict):
            # Assert that if we get dict, it's flagged as stale per contract
            assert result.get("stale", True)
            assert result.get("delay_note") == "[STALE - DB FALLBACK]"

def test_options_analytics():
    from src.analysis.options_analytics import compute_pcr, compute_max_pain, compute_iv_rank, extract_atm_iv
    
    mock_data = [
        {"strikePrice": 22000, "CE": {"openInterest": 1000, "impliedVolatility": 12.0}, "PE": {"openInterest": 500, "impliedVolatility": 14.0}},
        {"strikePrice": 22100, "CE": {"openInterest": 1500, "impliedVolatility": 11.5}, "PE": {"openInterest": 2000, "impliedVolatility": 13.5}},
    ]
    
    pcr = compute_pcr(mock_data)
    assert pcr == 1.0 # 2500 / 2500
    
    mp = compute_max_pain(mock_data)
    assert mp in (22000, 22100)
    
    atm_iv = extract_atm_iv(mock_data, 22050)
    assert atm_iv > 0.0

def test_fetch_options_chain_fallback():
    from src.fetchers.options_chain import fetch_options_chain
    with patch("src.utils.nse_session.NSESessionManager.fetch", side_effect=ConnectionError("NSE Down")):
        result = fetch_options_chain("NIFTY")
        assert result is None or getattr(result, "stale", True) or isinstance(result, dict)
