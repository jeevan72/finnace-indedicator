import requests
import json
from typing import List
from datetime import datetime

from utils.logger import get_logger
from utils.retry import retry
from utils.rate_limiter import rate_limit
from storage import models

logger = get_logger(__name__)

@rate_limit("ofac")
@retry(max_attempts=2, backoff_factor=3)
def _fetch_ofac_sdn_entities() -> list:
    """
    Very basic JSON/API wrapper to check OFAC Consolidated Screening List API.
    Since trade api requires no key for basic queries, we can use the ITA consolidated list.
    """
    url = "https://data.trade.gov/consolidated_screening_list/v1/search"
    # Search randomly for some major Russian/Iranian metal & oil giants common in tracking
    # e.g., "Rosneft", "Norilsk", etc. We just grab the latest additions if possible,
    # but the API doesn't easily sort by latest date. So we fetch a block of recent entities.
    
    # As an educational proxy, we'll search general lists
    params = {"sources": "SDN", "size": 100}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.warning(f"[{__name__}] OFAC screening API fetch failed: {e}")
        return []

def scan_sanctions_watch() -> List[dict]:
    """
    Pulls recent sanctioned entities flagged for metals/energy vectors.
    """
    results = []
    
    tracked_keywords = ["oil", "petroleum", "metal", "mining", "aluminum", "copper", "energy"]
    
    try:
        entities = _fetch_ofac_sdn_entities()
        
        for ent in entities:
            remarks = str(ent.get("remarks", "")).lower()
            programs = str(ent.get("programs", [])).lower()
            name = ent.get("name", "Unknown")
            
            # Check if entity remarks hit our commodity sectors
            matched_asset = None
            for kw in tracked_keywords:
                if kw in remarks or kw in programs:
                    matched_asset = kw.capitalize()
                    break
                    
            if matched_asset:
                start_dt_str = ent.get("start_date", None)
                added_dt = None
                if start_dt_str:
                    try:
                        added_dt = datetime.strptime(start_dt_str, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                
                raw = {
                    "entity_name": name,
                    "country": ", ".join(ent.get("addresses", [{}])[0].get("country", "") for _ in [1]) if ent.get("addresses") else "Unknown",
                    "asset_type": matched_asset,
                    "list_type": "SDN",
                    "added_date": added_dt,
                    "source": "ITA CSL API"
                }

                # Upsert into DB
                exists = models.SanctionsWatch.select().where(
                    (models.SanctionsWatch.entity_name == raw["entity_name"])
                ).exists()
                if not exists:
                    models.SanctionsWatch.create(**raw)
                    
                results.append(raw)
        
        return results
        
    except Exception as e:
        logger.error(f"[{__name__}] Sanctions scan failed: {e}")
        return _fallback_from_db()

def _fallback_from_db() -> List[dict]:
    try:
        records = models.SanctionsWatch.select().order_by(models.SanctionsWatch.id.desc()).limit(10)
        return [{"entity_name": r.entity_name, "asset_type": r.asset_type, "stale": True} for r in records]
    except Exception as e:
        logger.critical(f"[{__name__}] DB fallback failed for sanctions: {e}")
        return []
