"""Metric catalog: the business vocabulary of gold, mapped to us-gaap tags.

Companies (and the taxonomy) change tags over time, e.g. Apple's revenue is
SalesRevenueNet until FY2018, then RevenueFromContractWithCustomerExcludingAssessedTax
(ASC 606). `tags` are tried in order; the first one reported for a period wins.

statement:
  income / cashflow -> "flow" values measured over a period (duration facts).
                       10-Qs report them year-to-date, so quarters are derived.
  balance           -> "stock" values at a point in time (instant facts).
additive: False for per-share values; they cannot be subtracted into quarters.

To add a metric: append a Metric here. Nothing else changes.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    name: str
    label: str
    statement: str  # income | balance | cashflow
    tags: tuple[str, ...]
    unit: str = "USD"
    additive: bool = True


METRICS = [
    # Income statement (10-K Item 8 / 10-Q Part I Item 1: Statements of Operations)
    Metric("revenue", "Revenue", "income",
           ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet")),
    Metric("cost_of_revenue", "Cost of revenue", "income",
           ("CostOfGoodsAndServicesSold", "CostOfRevenue")),
    Metric("gross_profit", "Gross profit", "income", ("GrossProfit",)),
    Metric("research_and_development", "Research & development", "income",
           ("ResearchAndDevelopmentExpense",)),
    Metric("selling_general_admin", "Selling, general & admin", "income",
           ("SellingGeneralAndAdministrativeExpense",)),
    Metric("operating_expenses", "Operating expenses", "income", ("OperatingExpenses",)),
    Metric("operating_income", "Operating income", "income", ("OperatingIncomeLoss",)),
    Metric("income_tax", "Income tax", "income", ("IncomeTaxExpenseBenefit",)),
    Metric("net_income", "Net income", "income", ("NetIncomeLoss",)),
    Metric("eps_diluted", "Diluted EPS", "income", ("EarningsPerShareDiluted",),
           unit="USD/shares", additive=False),
    # Balance sheet
    Metric("cash", "Cash & equivalents", "balance", ("CashAndCashEquivalentsAtCarryingValue",)),
    Metric("current_assets", "Current assets", "balance", ("AssetsCurrent",)),
    Metric("total_assets", "Total assets", "balance", ("Assets",)),
    Metric("current_liabilities", "Current liabilities", "balance", ("LiabilitiesCurrent",)),
    Metric("total_liabilities", "Total liabilities", "balance", ("Liabilities",)),
    Metric("long_term_debt", "Term debt", "balance", ("LongTermDebt",)),
    Metric("commercial_paper", "Commercial paper", "balance", ("CommercialPaper",)),
    Metric("stockholders_equity", "Shareholders' equity", "balance", ("StockholdersEquity",)),
    # Cash flow statement (reported year-to-date only in 10-Qs)
    Metric("operating_cash_flow", "Operating cash flow", "cashflow",
           ("NetCashProvidedByUsedInOperatingActivities",)),
    Metric("capex", "Capital expenditures", "cashflow",
           ("PaymentsToAcquirePropertyPlantAndEquipment",)),
    Metric("buybacks", "Share repurchases", "cashflow", ("PaymentsForRepurchaseOfCommonStock",)),
    Metric("dividends", "Dividends paid", "cashflow", ("PaymentsOfDividends",)),
]

METRIC_NAMES = [m.name for m in METRICS]
