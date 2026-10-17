"""Gold: business-ready financials and KPIs, one row per company and fiscal period.

financials (long): cik, metric, fiscal_year, fiscal_period (Q1..Q4 | FY), value + lineage
    Flow metrics (income, cash flow) come from year-to-date values:
        FY = 12-month value from the 10-K
        Qn = YTD(n) - YTD(n-1)   e.g. Q4 = FY - 9-month YTD (no Q4 10-Q exists)
    Balance metrics are point-in-time: Qn = value at quarter end, FY = value at year end.
kpis (wide): one column per metric plus ratios (margins, net worth, FCF, growth...).
"""
from pyspark.sql import DataFrame, SparkSession, Window
import pyspark.sql.functions as F

from sec_edgar.config import settings
from sec_edgar.pipeline.metrics import METRIC_NAMES, METRICS
from sec_edgar.pipeline.silver import SILVER_FACTS

GOLD_FINANCIALS = f"{settings.gold_prefix}/financials"
GOLD_KPIS = f"{settings.gold_prefix}/kpis"
PERIOD = ["cik", "metric", "fiscal_year", "fiscal_period"]
LINEAGE = ["source_tag", "source_form", "source_accn", "filed"]


def metric_catalog(spark: SparkSession) -> DataFrame:
    rows = [(m.name, m.label, m.statement, m.unit, m.additive, tag, priority)
            for m in METRICS for priority, tag in enumerate(m.tags)]
    return spark.createDataFrame(
        rows, "metric string, label string, statement string, unit string, "
              "additive boolean, tag string, priority int")


def _best_tag(df: DataFrame) -> DataFrame:
    """Per period keep the highest-priority tag (lowest `priority`)."""
    w = Window.partitionBy(*PERIOD).orderBy("priority")
    return df.withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")


def _as_fy(df: DataFrame) -> DataFrame:
    return df.withColumn("fiscal_period", F.lit("FY"))


def build_financials(silver: DataFrame, catalog: DataFrame) -> DataFrame:
    facts = (
        silver.filter(F.col("fiscal_year").isNotNull())
        .join(catalog, (F.col("fact_name") == F.col("tag")) & (F.col("unit_type") == F.col("unit")))
        .select("cik", "metric", "statement", "additive", "priority", "fiscal_year",
                "fiscal_period", "duration_months", F.col("end").alias("period_end"),
                F.col("val").alias("value"), F.col("fact_name").alias("source_tag"),
                F.col("form").alias("source_form"), F.col("accn").alias("source_accn"), "filed")
        .withColumn("quarter", F.substring("fiscal_period", 2, 1).cast("int"))
    )
    is_balance = F.col("statement") == "balance"

    # Balance sheet: snapshot at each quarter end; the Q4 snapshot is also the FY value.
    balance = _best_tag(facts.filter(is_balance & F.col("duration_months").isNull()))
    balance = balance.unionByName(_as_fy(balance.filter("fiscal_period = 'Q4'")))

    # Per-share values: take reported 3-month and 12-month values as-is.
    flows = facts.filter(~is_balance)
    per_share = flows.filter(~F.col("additive"))
    per_share = _best_tag(per_share.filter("duration_months = 3")).unionByName(
        _as_fy(_best_tag(per_share.filter("duration_months = 12"))))

    # Additive flows: the year-to-date value for each quarter (3, 6, 9, 12 months).
    ytd = _best_tag(flows.filter(F.col("additive") & (F.col("duration_months") == F.col("quarter") * 3)))
    in_year = Window.partitionBy("cik", "metric", "fiscal_year").orderBy("quarter")
    quarterly = (
        ytd.withColumn("prev_value", F.lag("value").over(in_year))
        .withColumn("prev_quarter", F.lag("quarter").over(in_year))
        .withColumn("value", F.when(F.col("quarter") == 1, F.col("value"))
                    .when(F.col("prev_quarter") == F.col("quarter") - 1,
                          F.col("value") - F.col("prev_value")))  # gap in YTD -> null
        .filter(F.col("value").isNotNull())
        .drop("prev_value", "prev_quarter")
    )
    annual = _as_fy(ytd.filter("quarter = 4"))

    cols = PERIOD + ["period_end", "value"] + LINEAGE
    return (
        balance.select(*cols, F.lit(False).alias("is_derived"))
        .unionByName(per_share.select(*cols, F.lit(False).alias("is_derived")))
        .unionByName(annual.select(*cols, F.lit(False).alias("is_derived")))
        .unionByName(quarterly.select(*cols, (F.col("quarter") > 1).alias("is_derived")))
        .join(catalog.select("metric", "label", "statement").distinct(), "metric")
    )


def _ratio(num: str, den: str):
    return F.when(F.col(den) != 0, F.col(num) / F.col(den))


def build_kpis(financials: DataFrame) -> DataFrame:
    period = ["cik", "fiscal_year", "fiscal_period"]
    wide = (financials.groupBy(*period).pivot("metric", METRIC_NAMES).agg(F.first("value"))
            .join(financials.groupBy(*period).agg(F.max("period_end").alias("period_end")), period))

    same_period_last_year = Window.partitionBy("cik", "fiscal_period").orderBy("fiscal_year")

    def yoy(col: str):
        prev = F.lag(col).over(same_period_last_year)
        prev_year = F.lag("fiscal_year").over(same_period_last_year)
        return F.when((prev_year == F.col("fiscal_year") - 1) & (prev != 0), F.col(col) / prev - 1)

    return (
        wide.withColumns({
            "period_label": F.when(F.col("fiscal_period") == "FY",
                                   F.concat(F.lit("FY"), F.col("fiscal_year")))
                             .otherwise(F.concat_ws(" FY", F.col("fiscal_period"),
                                                    F.col("fiscal_year").cast("string"))),
            "gross_margin": _ratio("gross_profit", "revenue"),
            "operating_margin": _ratio("operating_income", "revenue"),
            "net_margin": _ratio("net_income", "revenue"),
            "rd_to_revenue": _ratio("research_and_development", "revenue"),
            "opex_to_revenue": _ratio("operating_expenses", "revenue"),
            "free_cash_flow": F.col("operating_cash_flow") - F.col("capex"),
            "net_worth": F.col("total_assets") - F.col("total_liabilities"),
            "total_debt": F.when(F.col("long_term_debt").isNotNull() | F.col("commercial_paper").isNotNull(),
                                 F.coalesce("long_term_debt", F.lit(0.0))
                                 + F.coalesce("commercial_paper", F.lit(0.0))),
            "current_ratio": _ratio("current_assets", "current_liabilities"),
            "shareholder_returns": F.col("buybacks") + F.col("dividends"),
            "revenue_yoy": yoy("revenue"),
            "net_income_yoy": yoy("net_income"),
        })
        .withColumns({
            "fcf_margin": _ratio("free_cash_flow", "revenue"),
            "debt_to_equity": _ratio("total_debt", "stockholders_equity"),
            # return on equity only makes sense on a full year of earnings
            "return_on_equity": F.when(F.col("fiscal_period") == "FY",
                                       _ratio("net_income", "stockholders_equity")),
        })
    )


def build_gold(spark: SparkSession) -> None:
    silver = spark.read.parquet(settings.s3a(SILVER_FACTS))
    financials = build_financials(silver, metric_catalog(spark)).cache()
    financials.write.mode("overwrite").parquet(settings.s3a(GOLD_FINANCIALS))
    build_kpis(financials).write.mode("overwrite").parquet(settings.s3a(GOLD_KPIS))
