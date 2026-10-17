"""python -m jobs.run_local [CIK ...] -- bronze JSON -> silver -> gold on your laptop, no S3.

Input:  data/facts/CIK{cik}_us_gaap.json   (python -m jobs.save_facts_json)
Output: data/gold/financials.parquet, data/gold/kpis.parquet   (read by the dashboard)

Same transforms as the S3 jobs. Results are written with pandas instead of Spark,
because Spark on Windows needs winutils.exe to write local files. One company is small.
"""
import sys
from pathlib import Path

from sec_edgar.pipeline.bronze import BRONZE_DDL
from sec_edgar.pipeline.gold import build_financials, build_kpis, metric_catalog
from sec_edgar.pipeline.silver import clean_facts
from sec_edgar.spark import get_spark
from sec_edgar.utils.logger import logger

FACTS_DIR = Path("data/facts")
GOLD_DIR = Path("data/gold")


def run_local(ciks: list[str]) -> None:
    spark = get_spark("local", s3=False)
    paths = [str(FACTS_DIR / f"CIK{cik.zfill(10)}_us_gaap.json") for cik in ciks]
    bronze = spark.read.schema(BRONZE_DDL).option("multiLine", True).json(paths)

    silver = clean_facts(bronze).cache()
    financials = build_financials(silver, metric_catalog(spark)).cache()
    kpis = build_kpis(financials)
    logger.info(f"bronze {bronze.count()} rows -> silver {silver.count()} -> "
                f"gold financials {financials.count()}")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in {"financials": financials, "kpis": kpis}.items():
        path = GOLD_DIR / f"{name}.parquet"
        df.toPandas().to_parquet(path, index=False)
        logger.info(f"Wrote {path}")


if __name__ == "__main__":
    run_local(sys.argv[1:] or ["0000320193"])  # default: Apple
