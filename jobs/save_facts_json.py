"""python -m jobs.save_facts_json [CIK ...] -- writes us-gaap facts to data/facts/.

Two files per CIK:
  CIK{cik}_companyfacts.json  raw API response
  CIK{cik}_us_gaap.json       flattened rows (one per reported value)
"""
import json
import sys
from pathlib import Path

from sec_edgar.edgar_api.facts import fetch_company_facts, flatten_us_gaap
from sec_edgar.utils.logger import logger

OUT_DIR = Path("data/facts")


def save_json(obj: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    logger.info(f"Wrote {path} ({path.stat().st_size / 1024:.1f} KB)")


def save_us_gaap_json(cik: str, out_dir: Path = OUT_DIR) -> None:
    cik = cik.zfill(10)
    company_facts = fetch_company_facts(cik)
    save_json(company_facts, out_dir / f"CIK{cik}_companyfacts.json")
    save_json(flatten_us_gaap(company_facts, cik), out_dir / f"CIK{cik}_us_gaap.json")


if __name__ == "__main__":
    for cik in sys.argv[1:] or ["0000320193"]:  # default: Apple
        save_us_gaap_json(cik)
