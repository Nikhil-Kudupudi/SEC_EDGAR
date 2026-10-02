"""Silver: typed + cleaned facts. TODO next: dedupe restated facts (see below)."""
import pyspark.sql.functions as sf

from sec_edgar.config import settings
from sec_edgar.pipeline.bronze import BRONZE_FACTS

SILVER_FACTS = f"{settings.silver_prefix}/us_gaap_facts"


def build_silver(spark) -> None:
    df = spark.read.parquet(settings.s3a(BRONZE_FACTS))
    df = df.withColumns({"start": sf.to_date("start"), "end": sf.to_date("end"),
                         "filed": sf.to_date("filed")})
    # TODO: dedupe on (cik, fact_name, start, end, fy, fp) keeping latest `filed`.
    df.write.mode("overwrite").parquet(settings.s3a(SILVER_FACTS))
