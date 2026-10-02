from sec_edgar.sec.client import get_json
from sec_edgar.utils.logger import logger


def fetch_company_facts(cik: str) -> dict:
    """Raw companyfacts JSON for a 10-digit zero-padded CIK."""
    return get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")


def flatten_us_gaap(company_facts: dict, cik: str) -> list[dict]:
    """One row per reported value. Pure function: dict in, rows out (no network)."""
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    rows = []
    for fact_name, fact in us_gaap.items():
        for unit_type, units in fact["units"].items():
            for unit in units:
                rows.append({
                    "cik": cik, "fact_name": fact_name, "label": fact["label"],
                    "unit_type": unit_type, **unit, "val": float(unit["val"]),
                })
    logger.info(f"CIK {cik}: {len(us_gaap)} us-gaap facts -> {len(rows)} rows")
    return rows


def get_us_gaap_facts(cik: str) -> list[dict]:
    return flatten_us_gaap(fetch_company_facts(cik), cik)
