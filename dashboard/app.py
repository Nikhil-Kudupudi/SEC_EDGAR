"""streamlit run dashboard/app.py -- executive view of one company's gold KPIs.

Reads gold produced by `python -m jobs.run_local` (data/gold) or by the S3 jobs
(set GOLD_DIR=s3://<bucket>/gold). The dashboard only reads gold: no business logic here.
"""
import os

import pandas as pd
import streamlit as st

GOLD_DIR = os.getenv("GOLD_DIR", "data/gold")
BILLION = 1e9


@st.cache_data
def load(name: str) -> pd.DataFrame:
    path = f"{GOLD_DIR}/{name}.parquet" if GOLD_DIR.startswith("data") else f"{GOLD_DIR}/{name}"
    return pd.read_parquet(path)


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
