import polars as pl

from sec_edgar.config import settings
from sec_edgar.sec.client import get_json
from sec_edgar.storage.parquet import export_parquet
from sec_edgar.utils.logger import logger

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def get_company_tickers() -> pl.DataFrame:
    rows = [{**t, "cik_str": str(t["cik_str"]).zfill(10)} for t in get_json(TICKERS_URL).values()]
    return pl.DataFrame(rows)


def save_tickers_master() -> None:
    df = get_company_tickers()
    logger.info(f"Retrieved {len(df)} company tickers.")
    export_parquet(df, bucket=settings.bucket, prefix=settings.raw_prefix,
                   file_prefix="company_tickers_master")
