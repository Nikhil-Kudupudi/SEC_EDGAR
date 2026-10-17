# SEC_EDGAR

Turns SEC EDGAR XBRL filings (10-K / 10-Q) into executive KPIs: revenue, operating
expenses, margins, net worth, free cash flow and growth. The sample company is Apple
(CIK 0000320193).

Medallion layers: **raw → bronze** (as filed) → **silver** (clean, deduped, fiscal periods;
PySpark) → **gold** (financials + KPIs; PySpark) → **dashboard** (Streamlit).

- Why each rule exists, the finance references, and the KPI formulas: [docs/pipeline.md](docs/pipeline.md)
- Vocabulary: [CONTEXT.md](CONTEXT.md)

## Run (one company, local)
```bash
uv sync
python -m jobs.save_facts_json 0000320193   # download Apple facts -> data/facts/
python -m jobs.run_local 0000320193         # silver + gold -> data/gold/
streamlit run dashboard/app.py
```

## Run (S3 lake)
```bash
python -m jobs.run_bronze 0000320193
python -m jobs.run_silver
python -m jobs.run_gold
GOLD_DIR=s3://secedgar-nikhil/gold streamlit run dashboard/app.py
```

## Local Spark on Windows
- `SPARK_HOME` must point to a Spark version that matches the `pyspark` package. Here
  `C:\spark\spark-3.5.7` was loaded instead of the venv's pyspark.
- The Python workers have to use the venv interpreter. `get_spark()` sets `PYSPARK_PYTHON`
  to it, but the worker still crashed in the last test, so this is not solved yet.
- Spark needs `winutils.exe` (`HADOOP_HOME`) to write local files. That is why
  `run_local` writes its output with pandas.
