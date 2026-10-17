# Glossary

Terms used in code and docs. Pipeline reasoning: `docs/pipeline.md`.

- **CIK**: SEC Central Index Key, the company id. Always 10 digits, zero-padded (Apple = `0000320193`).
- **Fact / tag** (`fact_name`): one us-gaap XBRL element, e.g. `NetIncomeLoss`.
- **Metric**: a business name in gold (e.g. `revenue`) mapped to one or more tags in `metrics.py`.
- **Form**: filing type. **10-K** = annual (audited), **10-Q** = quarterly (Q1–Q3), **/A** = amendment, **8-K** = current report (not used).
- **accn**: accession number, the unique id of one filing.
- **filed**: date the filing was submitted. Used to pick the latest (restated) value.
- **Instant fact**: point-in-time value (balance sheet). No `start`.
- **Duration fact**: value over `start`→`end` (income statement, cash flow). `duration_months` ∈ {3, 6, 9, 12}.
- **YTD**: year-to-date duration (6 or 9 months) reported in 10-Qs.
- **Filing fy/fp** (bronze `fy`, `fp`): fiscal year/period of the *filing*, not of the value.
- **fiscal_year / fiscal_period** (silver/gold): fiscal year and quarter (Q1–Q4, or FY in gold) *of the value*.
- **Derived quarter**: a quarterly flow computed as YTD(n) − YTD(n−1). Flagged `is_derived`.
- **Net worth**: total assets − total liabilities (= shareholders' equity, book value).
- **Free cash flow**: operating cash flow − capital expenditures.
