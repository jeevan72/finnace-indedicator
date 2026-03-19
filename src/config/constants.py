# Corporate Announcement Filter Keywords (Match Subject Line Only)
ANNOUNCEMENT_KEYWORDS = {
    "corporate_action": ["dividend", "bonus", "split", "rights issue", "buyback"],
    "fund_raising": ["qip", "fpo", "ncd", "preferential allotment", "fccb"],
    "governance": ["agm", "egm", "board meeting", "change in management"],
    "deal": ["merger", "acquisition", "demerger", "amalgamation", "takeover"],
    "regulatory": ["sebi order", "cci approval", "nclt", "insolvency"],
    "results": ["financial results", "quarterly results", "auditor"]
}

# Supply Signal Thresholds
SUPPLY_THRESHOLDS = {
    "eia_crude_draw_bullish_mmbbl": 2.0,
    "eia_crude_build_bearish_mmbbl": 3.0,
    "opec_cut_bullish_kbpd": 500,
    "opec_hike_bearish_kbpd": 500,
    "metals_lme_stock_draw_pct": -10.0 # week-over-week
}

# Geopolitical Risk Scoring Multipliers
RISK_MULTIPLIERS = {
    "sanctions_active": 30,
    "risk_level_high": 25,
    "risk_level_medium": 15,
    "india_import_share_high": 20, # threshold > 20%
    "relation_level_strained": 10
}
