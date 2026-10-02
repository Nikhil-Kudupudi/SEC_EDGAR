"""Bronze: us-gaap facts flattened from SEC JSON. No business rules here.

- Fixed schema: every write has the same column types, so files never conflict.
- Partitioned by fy and form (low cardinality). cik is NOT a partition (thousands).
- Files are named `{cik}_<n>.parquet`, so one company's data can be replaced
  (delete its files, write new ones) without touching other companies.
"""
import polars as pl

from sec_edgar.config import settings
from sec_edgar.sec.facts import get_us_gaap_facts
from sec_edgar.storage.parquet import export_parquet

BRONZE_FACTS = f"{settings.bronze_prefix}/us_gaap_facts"
PARTITION_COLS = ["fy", "form"]

BRONZE_SCHEMA = {
    "cik": pl.Utf8, "fact_name": pl.Utf8, "label": pl.Utf8, "unit_type": pl.Utf8,
    "start": pl.Utf8, "end": pl.Utf8, "val": pl.Float64, "accn": pl.Utf8,
    "fy": pl.Int64, "fp": pl.Utf8, "form": pl.Utf8, "filed": pl.Utf8, "frame": pl.Utf8,
}


def build_bronze(ciks: list[str]) -> None:
    for cik in ciks:
        df = pl.from_dicts(get_us_gaap_facts(cik), schema=BRONZE_SCHEMA)
        export_parquet(df, bucket=settings.bucket, prefix=BRONZE_FACTS,
                       file_prefix=cik, partition_cols=PARTITION_COLS)
