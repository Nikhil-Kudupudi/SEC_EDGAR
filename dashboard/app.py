"""streamlit run dashboard/app.py -- executive view of one company's gold KPIs.

Reads gold from S3 (s3://<S3_BUCKET>/gold/{financials,kpis}/, written by the Spark jobs).
Set GOLD_DIR to override, e.g. GOLD_DIR=data/gold for local runs.
AWS credentials come from .env / the standard AWS environment variables.
The dashboard only reads gold: no business logic here.
"""
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BUCKET = os.getenv("S3_BUCKET", "secedgar-nikhil")
GOLD_DIR = os.getenv("GOLD_DIR", f"s3://{BUCKET}/gold").rstrip("/")
BILLION = 1e9


def _storage_options() -> dict | None:
    if not GOLD_DIR.startswith("s3://"):
        return None
    key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET")
    # without explicit keys s3fs falls back to the default AWS credential chain
    return {"key": key, "secret": secret} if key and secret else {}


@st.cache_data(ttl=600, show_spinner="Loading gold from S3...")
def load(name: str) -> pd.DataFrame:
    # Spark writes each gold table as a folder of parquet part files; pyarrow reads the folder.
    return pd.read_parquet(f"{GOLD_DIR}/{name}/", storage_options=_storage_options())


st.set_page_config(page_title="SEC EDGAR financials", layout="wide")  # must be first st call
kpis = load("kpis")
financials = load("financials")
cik = st.sidebar.selectbox("Company (CIK)", sorted(kpis["cik"].unique()))
view = st.sidebar.radio("Periods", ["Annual (10-K)", "Quarterly"])

company = kpis[kpis["cik"] == cik]
data = (company[company["fiscal_period"] == "FY"] if view.startswith("Annual")
        else company[company["fiscal_period"] != "FY"])
data = data.sort_values("period_end").set_index("period_label")
latest = data.iloc[-1]

st.title(f"CIK {cik} · {latest.name}")
st.caption("Source: SEC EDGAR XBRL company facts (us-gaap), from 10-K and 10-Q filings. "
           "USD billions unless noted.")

# --- headline tiles: latest period, with year-over-year change where available
tiles = st.columns(5)
for col, (label, field, delta) in zip(tiles, [
    ("Revenue", "revenue", "revenue_yoy"),
    ("Net income", "net_income", "net_income_yoy"),
    ("Operating expenses", "operating_expenses", None),
    ("Free cash flow", "free_cash_flow", None),
    ("Net worth (equity)", "net_worth", None),
]):
    value = latest[field]
    change = latest[delta] if delta else None
    col.metric(label, "n/a" if pd.isna(value) else f"${value / BILLION:,.1f}B",
               None if change is None or pd.isna(change) else f"{change:+.1%} YoY")

# --- trends
left, right = st.columns(2)
left.subheader("Revenue, operating expenses, net income")
left.line_chart(data[["revenue", "operating_expenses", "net_income"]] / BILLION)
right.subheader("Margins")
right.line_chart(data[["gross_margin", "operating_margin", "net_margin"]])

left, right = st.columns(2)
left.subheader("Where operating spend goes")
left.bar_chart(data[["research_and_development", "selling_general_admin"]] / BILLION)
right.subheader("Cash generation vs. returned to shareholders")
right.bar_chart(data[["free_cash_flow", "buybacks", "dividends"]] / BILLION)

left, right = st.columns(2)
left.subheader("Balance sheet")
left.line_chart(data[["total_assets", "total_liabilities", "net_worth"]] / BILLION)
right.subheader("Liquidity and leverage")
right.line_chart(data[["current_ratio", "debt_to_equity"]])

# --- lineage: every number traces back to a filing
with st.expander("Lineage: which filing and us-gaap tag each number came from"):
    period = st.selectbox("Period", data.index[::-1])
    row = data.loc[period]
    st.dataframe(
        financials[(financials["cik"] == cik) & (financials["fiscal_year"] == row["fiscal_year"])
                   & (financials["fiscal_period"] == row["fiscal_period"])]
        [["label", "value", "source_tag", "source_form", "source_accn", "filed", "is_derived"]]
        .sort_values("label"),
        hide_index=True,
    )
