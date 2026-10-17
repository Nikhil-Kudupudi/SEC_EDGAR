"""Silver: one clean, typed value per (company, fact, unit, period).

Bronze keeps every value exactly as filed. The same number shows up many times,
because each 10-K/10-Q repeats prior periods as comparatives and later filings
may restate them. Silver applies four rules (see docs/pipeline.md):

1. Keep only periodic financial reports: 10-K, 10-Q and their amendments (/A).
   8-K earnings releases are unaudited and duplicate the 10-Q/10-K numbers.
2. Describe the period by its dates, not the filing: `duration_months`
   (3, 6, 9, 12; null for balance-sheet "instant" values).
3. Dedupe: per (cik, fact_name, unit_type, start, end) keep the latest-filed value,
   so restatements and amendments win.
4. Attach the fiscal year/period OF THE VALUE (bronze `fy`/`fp` describe the filing).
   A filing's own period ends on the latest `end` it reports; at that date the
   filing's fy/fp are correct, which gives a calendar end-date -> (fiscal_year, fiscal_period).
"""
from pyspark.sql import DataFrame, Window
import pyspark.sql.functions as F

from sec_edgar.config import settings
from sec_edgar.pipeline.bronze import BRONZE_FACTS

SILVER_FACTS = f"{settings.silver_prefix}/us_gaap_facts"
FINANCIAL_FORMS = ["10-K", "10-K/A", "10-Q", "10-Q/A"]
FACT_KEY = ["cik", "fact_name", "unit_type", "start", "end"]


def fiscal_calendar(facts: DataFrame) -> DataFrame:
    """(cik, end) -> fiscal_year, fiscal_period for every period end a filing covers.
    fiscal_period is Q1..Q4; a 10-K's own period (fp=FY) is the year's Q4 end."""
    report_end = Window.partitionBy("cik", "accn")
    return (
        facts.withColumn("report_end", F.max("end").over(report_end))
        .filter((F.col("end") == F.col("report_end")) & F.col("fp").isNotNull())
        .select("cik", "end", F.col("fy").alias("fiscal_year"),
                F.when(F.col("fp") == "FY", "Q4").otherwise(F.col("fp")).alias("fiscal_period"))
        .groupBy("cik", "end")  # 10-K and 10-K/A can share an end date
        .agg(F.max("fiscal_year").alias("fiscal_year"), F.max("fiscal_period").alias("fiscal_period"))
    )


def clean_facts(bronze: DataFrame) -> DataFrame:
    """Pure transform: bronze facts in, silver facts out (no I/O, easy to test)."""
    facts = (
        bronze.filter(F.col("form").isin(FINANCIAL_FORMS))
        .withColumns({"start": F.to_date("start"), "end": F.to_date("end"),
                      "filed": F.to_date("filed")})
        # 91 days -> 3, 182 -> 6, 273 -> 9, 364 -> 12 (52/53-week years round the same)
        .withColumn("duration_months",
                    F.round(F.datediff("end", "start") / 30.44).cast("int"))
    )

    latest_first = Window.partitionBy(*FACT_KEY).orderBy(F.col("filed").desc(), F.col("accn").desc())
    deduped = (facts.withColumn("rn", F.row_number().over(latest_first))
               .filter("rn = 1").drop("rn"))

    return (
        deduped.join(fiscal_calendar(facts), ["cik", "end"], "left")
        .select("cik", "fact_name", "label", "unit_type", "start", "end", "duration_months",
                "val", "fiscal_year", "fiscal_period",
                "form", "accn", "filed", "frame")
    )


def build_silver(spark) -> None:
    bronze = spark.read.parquet(settings.s3a(BRONZE_FACTS))
    clean_facts(bronze).write.mode("overwrite").partitionBy("fiscal_year") \
        .parquet(settings.s3a(SILVER_FACTS))
