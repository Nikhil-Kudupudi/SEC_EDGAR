# Pipeline: how Apple's SEC filings become executive KPIs

This document explains **what** each layer does and **why**, with the finance reasoning
behind every rule. Code lives in `sec_edgar/pipeline/`; vocabulary is in `CONTEXT.md`.

Sample company: **Apple Inc., CIK 0000320193**. Fiscal year ends on the last Saturday of
September (52/53 weeks), so "FY2024" ran from 2023-10-01 to 2024-09-28.

```
SEC API ──► raw ──► bronze ──────────► silver ─────────────► gold ─────────────► dashboard
 companyfacts   flattened rows     one clean value       financials + kpis     streamlit
 JSON           (as filed)         per fact & period     (business metrics)
 edgar_api/     bronze.py          silver.py (PySpark)   gold.py + metrics.py  dashboard/app.py
```

| Run | Command |
|---|---|
| Local, one company, no S3 | `python -m jobs.save_facts_json` then `python -m jobs.run_local` |
| S3 lake | `python -m jobs.run_bronze` → `jobs.run_silver` → `jobs.run_gold` |
| Dashboard | `streamlit run dashboard/app.py` |

---

## 1. Source and references

**Data source:** SEC EDGAR XBRL "company facts" API
(`https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`). Every number a company
tags in its filings, grouped by taxonomy (`us-gaap`, `dei`, …), then by tag, then by unit.
We use the `us-gaap` taxonomy only (see `domain_info.md`).

**Which filings matter (form types):**

| Form | What it is | Audited? | Used? |
|---|---|---|---|
| **10-K** | Annual report. Item 8 holds the audited financial statements. | Yes | ✅ source of FY numbers |
| **10-Q** | Quarterly report for Q1, Q2 and Q3 (no Q4 10-Q exists; Q4 is inside the 10-K). | Reviewed, not audited | ✅ source of quarters |
| **10-K/A, 10-Q/A** | Amendments that correct an earlier filing. | — | ✅ they replace the original |
| **8-K** | Current report. For Apple these facts come from earnings press releases. | No | ❌ dropped: duplicates 10-Q/10-K, unaudited |

Apple's file: 25,046 rows and 503 us-gaap tags. By form: 15,251 from 10-Q, 8,469 from 10-K,
1,118 from 8-K and 208 from 10-K/A.

**References used for the finance logic:**
- SEC EDGAR API docs: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>
  (meaning of `fy`, `fp`, `form`, `frame`, `accn`, `filed`).
- FASB US GAAP Financial Reporting Taxonomy: tag definitions such as `Revenues`,
  `RevenueFromContractWithCustomerExcludingAssessedTax` (ASC 606), `OperatingIncomeLoss`.
  Browse at <https://xbrlview.fasb.org>.
- Apple's FY2024 Form 10-K (accession 0000320193-24-000123, filed 2024-11-01), Item 8.
  Use it to check gold numbers by hand, e.g. revenue **$391,035M** and net income **$93,736M**.

---

## 2. Bronze: as filed, no business rules (`bronze.py`)

One row per reported value: `cik, fact_name, label, unit_type, start, end, val, accn, fy,
fp, form, filed, frame`. Nothing is removed or interpreted, so bronze can always be
re-processed if a rule in silver/gold turns out to be wrong.

---

## 3. Silver: one trustworthy value per fact and period (`silver.py`, PySpark)

Bronze is noisy in three finance-specific ways. Silver fixes each with one rule.

### Rule 1: keep only periodic reports (`FINANCIAL_FORMS`)
Keep 10-K, 10-Q and their /A amendments. Drop 8-K (see the table above).

### Rule 2: describe the period by its dates (`duration_months`)
- **Instant** facts (balance sheet: assets, equity, cash) have no `start`. They are a
  snapshot at `end`, so `duration_months` is null.
- **Duration** facts (income statement, cash flow) cover `start`→`end`.
  `round(days / 30.44)` gives **3, 6, 9 or 12** months. This works for 52/53-week years
  too (Apple's 14-week Q1 FY2023 is 98 days, which still rounds to 3).

Why this matters: a Q3 10-Q reports revenue twice, once for the 3 months and once for the
9 months year-to-date. Both carry `fp = Q3`, so only the dates tell them apart.

### Rule 3: dedupe, latest filing wins
Each filing repeats prior periods as comparatives. Apple's FY2022 revenue appears in the
FY2022, FY2023 and FY2024 10-Ks. Key = `(cik, fact_name, unit_type, start, end)`. We keep
the row with the latest `filed`, which means **restatements and amendments override**
the original numbers. An analyst does the same thing by reading the most recent 10-K.

### Rule 4: fiscal year/period of the VALUE, not the filing
⚠️ Bronze `fy`/`fp` describe the **filing**. In the FY2024 10-K, the FY2022 revenue row
has `fy = 2024`. Grouping by bronze `fy` would mix three different years.

Fix (`fiscal_calendar`): a filing's own period ends on the latest `end` it reports. Only on
that date are its `fy`/`fp` correct for the data. Collecting those gives a lookup
`(cik, end date) → (fiscal_year, fiscal_period)`, joined onto every fact. `fp = FY` maps to
`Q4` because a year-end date is also the end of the fourth quarter.

Limitation: values whose end date is not the period of any filing in the data (e.g.
FY2008 comparatives in Apple's first XBRL filing) get a null fiscal year. Gold skips them.

**Silver output** (`silver/us_gaap_facts`, partitioned by `fiscal_year`):
`cik, fact_name, label, unit_type, start, end, duration_months, val, fiscal_year,
fiscal_period, form, accn, filed, frame`.

---

## 4. Gold: business metrics executives recognize (`metrics.py`, `gold.py`)

### 4a. Metric catalog (`metrics.py`): tag → business name
Executives say "revenue", not `RevenueFromContractWithCustomerExcludingAssessedTax`.
The catalog maps each metric to a **priority list** of tags because tags change over time:

| Metric | Tags (first one found wins) | Why several |
|---|---|---|
| revenue | `RevenueFromContractWithCustomerExcludingAssessedTax`, `Revenues`, `SalesRevenueNet` | ASC 606 (2018) replaced `SalesRevenueNet`; Apple used `Revenues` in FY2018 |
| cost_of_revenue | `CostOfGoodsAndServicesSold`, `CostOfRevenue` | different companies use different tags |
| others | one tag each (see file) | stable for Apple |

Each metric belongs to a statement:
- **income**: revenue, cost of revenue, gross profit, R&D, SG&A, operating expenses, operating income, income tax, net income, diluted EPS
- **balance**: cash, current/total assets, current/total liabilities, term debt, commercial paper, equity
- **cashflow**: operating cash flow, capex, buybacks, dividends

Adding a metric = one line in `METRICS`. This is the main extension point (open/closed).

### 4b. `gold/financials`: long table, one row per metric × fiscal period
Columns: `cik, metric, label, statement, fiscal_year, fiscal_period (Q1–Q4 | FY),
period_end, value, source_tag, source_form, source_accn, filed, is_derived`.

How each kind of value is computed:

| Kind | FY | Quarter Qn |
|---|---|---|
| **Balance** (instant) | snapshot at year end (= the Q4 snapshot) | snapshot at quarter end |
| **Flow** (income, cash flow) | 12-month value from the 10-K | **YTD(n) − YTD(n−1)** |
| **Per-share** (EPS) | 12-month value as reported | 3-month value as reported. Q4 is not derived. |

Why YTD differencing for flows:
- Apple files **no Q4 10-Q**, so Q4 = FY (10-K) − 9-month YTD (Q3 10-Q).
- 10-Q **cash flow statements are year-to-date only**: Q2 shows 6 months, never the
  3-month quarter. Differencing is the only way to get quarterly cash flow.
- One rule covers both income and cash flow. Q1 is reported directly. If a YTD value is
  missing, the next quarter becomes null rather than wrong.
- EPS is a ratio, so subtracting EPS values gives a wrong answer. It is excluded from
  differencing (`additive=False`).

**Lineage:** each row keeps the tag, form, accession number and filing date it came from,
plus `is_derived` for computed quarters. Any number on the dashboard can be traced to a
specific SEC filing. That traceability is the main value of the product for finance users.

### 4c. `gold/kpis`: wide table, one row per company × fiscal period
All catalog metrics as columns, plus:

| KPI | Formula | Executive question it answers |
|---|---|---|
| gross_margin | gross_profit / revenue | How much of each sales dollar is left after making the product? |
| operating_margin | operating_income / revenue | How profitable is the core business? |
| net_margin | net_income / revenue | Bottom-line profitability |
| rd_to_revenue, opex_to_revenue | R&D or opex / revenue | How much do we reinvest, and is spending disciplined? |
| free_cash_flow | operating_cash_flow − capex | Cash actually generated |
| fcf_margin | free_cash_flow / revenue | Cash conversion |
| **net_worth** | total_assets − total_liabilities | Book value, which equals shareholders' equity |
| total_debt | term debt + commercial paper | Leverage |
| debt_to_equity | total_debt / equity | Balance-sheet risk |
| current_ratio | current_assets / current_liabilities | Short-term liquidity |
| return_on_equity | net_income / equity (FY only) | Return on shareholders' capital |
| shareholder_returns | buybacks + dividends | Cash returned to owners |
| revenue_yoy, net_income_yoy | vs. same period last year | Growth, comparing like with like (Q3 vs Q3) |

Ratios are null when the denominator is 0 or missing. YoY is null when the prior year is
missing.

Note for Apple: equity is small relative to assets because of large buybacks, so ROE and
debt-to-equity look extreme. That is a correct result, not a bug, and worth explaining to
an executive audience.

---

## 5. Dashboard (`dashboard/app.py`)
Reads gold only (no business logic). It shows headline tiles (latest period with YoY),
revenue/opex/net income trends, margins, the R&D vs SG&A split, FCF vs shareholder returns,
the balance sheet, liquidity/leverage, and a lineage table that traces each number to a
filing. It has an Annual (10-K) / Quarterly toggle.

---

## 6. Design principles applied
- **Layers have one job each.** Bronze = as filed, silver = correct, gold = meaningful.
- **Pure transforms, I/O at the edges.** `clean_facts`, `build_financials` and
  `build_kpis` take DataFrames and return DataFrames. `build_*` / `jobs/` do the reads and
  writes, so the same logic runs on S3 or on a local file (`jobs/run_local.py`).
- **Configuration as data.** The metric catalog drives gold. New metrics need no code changes.
- **Single source of settings** (`config.py`) and a single SparkSession factory (`spark.py`).

## 7. How to verify (manual checks against the 10-K)
For FY2024 in `data/gold/kpis.parquet`, expect revenue 391,035M, cost of revenue 210,352M,
gross profit 180,683M, R&D 31,370M, SG&A 26,097M, operating expenses 57,467M, operating
income 123,216M, net income 93,736M, total assets 364,980M, total liabilities 308,030M,
equity 56,950M and diluted EPS $6.08. Also check that Q1+Q2+Q3+Q4 = FY for revenue.

## 8. Not done yet / next steps
- **Pipeline not executed yet.** The local Spark run failed on Python-worker setup (see
  README "Local Spark on Windows"). The numbers above have not been checked against output.
- **dbt:** move the gold SQL-style logic (KPIs) to dbt models over silver
  (dbt-duckdb or dbt-spark), with tests such as `unique(cik, fiscal_year, fiscal_period)`
  and `not_null(revenue)`. PySpark stays for bronze→silver.
- **Company name/ticker** in gold (join `company_tickers_master`).
- **More companies:** the logic is not Apple-specific, but the metric catalog may need more
  fallback tags (e.g. banks don't report `GrossProfit`).
- **Orchestration (Airflow)** once the three jobs are stable.
- **Automated tests** with a tiny hand-made fixture (a few rows covering restatement, YTD, 8-K).
