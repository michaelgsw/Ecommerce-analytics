# Dashboard Data Validation

Run (UTC): 2026-10-07T23:25:24+00:00.

**PASS: 54 source/projection/reconciliation checks and nine exact CSV readbacks; zero failures.**

## Method and unchanged definitions

The builder reads all nine prior analytics CSVs, compares every field against the previously validated JSON results, and verifies source/query/export hashes and prior check outcomes. It also reads the validated aggregate results that were intentionally retained only in customer_analysis_validation.json: Pareto points, interval distributions, category transitions and category mixes. No SQLite connection, source query or business eligibility change is needed.

The separate validator imports no dashboard preparation functions. It checks projected values/types/NULLs against original analytical evidence, aggregate grain uniqueness, exact monetary/count rollups, fixed share denominators, all Pareto points, conditional interval denominators and every cohort cell. Source and export ratios retain exact integer components. CSV blank means SQL/analytical NULL, never an invented numeric zero.

Category rows have three separate scopes: All completed, One-time, Repeat. All completed duplicates the combined group sales and must never be summed with group rows. Category customer/order counts overlap across categories. Segment customers/orders/sales are additive because the four segments are mutually exclusive. Monthly distinct customers are not additive. Concentration points are cumulative and not additive. Cohort size is repeated across offsets and must be summed at M0 only; each rate keeps its original cohort denominator.

The monthly display series suppresses gaps and post-completed-window unresolved outcomes with NULL; original observed item_sales_hundredths and flags remain unchanged. This is a separate chart field, not a revised KPI. Boundary observed sales remain visible with warnings. All monetary totals and rational components import as Whole number. Decimal ratios in DAX are display calculations; the validated six-place KPI text remains Text.

## Reconciled totals

- Completed orders: 96,478; persistent completed customers: 93,358.
- Delivered item sales: 1,322,149,811 hundredths; repeat customers: 2,801.
- All-status orders: 99,441. Delivered rate denominator remains all-status orders.
- Four segment totals and M0 cohort sizes reproduce the completed-customer population.
- First-to-second category pairs: 2,801; first-to-second timing bins: 2,801; all consecutive timing bins: 3,120.

## Files, row counts and grains

- data/dashboard/dashboard_kpis.csv: 7 rows; key/grain: metric_key.
- data/dashboard/dashboard_monthly_sales.csv: 26 rows; key/grain: month.
- data/dashboard/dashboard_customer_segments.csv: 4 rows; key/grain: segment.
- data/dashboard/dashboard_customer_concentration.csv: 101 rows; key/grain: record_type, target_customer_percent.
- data/dashboard/dashboard_cohorts.csv: 552 rows; key/grain: cohort_month, month_index.
- data/dashboard/dashboard_repeat_timing.csv: 23 rows; key/grain: record_type, scope, metric.
- data/dashboard/dashboard_categories.csv: 218 rows; key/grain: customer_type, category_key.
- data/dashboard/dashboard_category_transition.csv: 4 rows; key/grain: behavior.
- data/dashboard/dashboard_order_status.csv: 8 rows; key/grain: order_status.

dashboard_manifest.json records exact headers, Power BI types, NULL support, grains, input hashes and export hashes. No customer/order/product/seller identifiers are exported.

## Check outcomes

- PASS: Prior CSV/evidence/hash: sales_overview.csv.
- PASS: Prior CSV/evidence/hash: monthly_sales.csv.
- PASS: Prior CSV/evidence/hash: category_performance.csv.
- PASS: Prior CSV/evidence/hash: customer_overview.csv.
- PASS: Prior CSV/evidence/hash: order_status_summary.csv.
- PASS: Prior CSV/evidence/hash: customer_segments.csv.
- PASS: Prior CSV/evidence/hash: customer_cohort_summary.csv.
- PASS: Prior CSV/evidence/hash: cohort_retention_matrix.csv.
- PASS: Prior CSV/evidence/hash: repeat_purchase_summary.csv.
- PASS: Seven unique KPI keys.
- PASS: All KPI rational components/populations/units.
- PASS: KPI display text equals prior validated values.
- PASS: Unambiguous KPI labels.
- PASS: KPI population-specific period labels; no completed date assigned to operations.
- PASS: dashboard_monthly_sales: every projected value/type/NULL.
- PASS: Monthly sales/orders exactly additive; distinct monthly customers not summed.
- PASS: dashboard_customer_segments: every projected value/type/NULL.
- PASS: Segment customer/order/sales totals.
- PASS: One-time: weighted means retain original denominators.
- PASS: Repeat: weighted means retain original denominators.
- PASS: All 100 cumulative Pareto points exactly preserved.
- PASS: Pareto monotonic endpoints.
- PASS: Top 1/5/10/20 highlight labels.
- PASS: Actual 80% threshold exactly retained.
- PASS: dashboard_cohorts: every projected value/type/NULL.
- PASS: Only M0 cohort sizes are additive.
- PASS: Every cohort-cell denominator equals its original cohort size.
- PASS: Unavailable cohort rates/counts stay NULL.
- PASS: Future observed counts stay NULL.
- PASS: M1: common-cohort card returns and original-size denominator.
- PASS: M2: common-cohort card returns and original-size denominator.
- PASS: M3: common-cohort card returns and original-size denominator.
- PASS: All nine timing metrics retain exact counts and rational pairs.
- PASS: Timing summary units, scope and window ordering.
- PASS: All fourteen interval bins retain scope/count/range.
- PASS: first_to_second: mutually exclusive timing bins and conditional denominators.
- PASS: all_consecutive: mutually exclusive timing bins and conditional denominators.
- PASS: Every category scope/key/value/rank/NULL/translation flag.
- PASS: All completed: category sales additive with fixed full-group denominator.
- PASS: One-time: category sales additive with fixed full-group denominator.
- PASS: Repeat: category sales additive with fixed full-group denominator.
- PASS: dashboard_category_transition: every projected value/type/NULL.
- PASS: Category transitions: one pair per observed repeat customer.
- PASS: dashboard_order_status: every projected value/type/NULL.
- PASS: Status counts cover all orders.
- PASS: dashboard_kpis: unique documented aggregate grain.
- PASS: dashboard_monthly_sales: unique documented aggregate grain.
- PASS: dashboard_customer_segments: unique documented aggregate grain.
- PASS: dashboard_customer_concentration: unique documented aggregate grain.
- PASS: dashboard_cohorts: unique documented aggregate grain.
- PASS: dashboard_repeat_timing: unique documented aggregate grain.
- PASS: dashboard_categories: unique documented aggregate grain.
- PASS: dashboard_category_transition: unique documented aggregate grain.
- PASS: dashboard_order_status: unique documented aggregate grain.
- PASS: nine saved CSVs reread field by field, preserving headers, row order, exact integers and blanks.
- PASS: all 41 protected inputs retain identical before/after SHA-256 hashes.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m src.dashboard.build_dashboard_data
.\.venv\Scripts\python.exe -m src.dashboard.build_dashboard_data --validate-only
```

Files are staged/read back before individual replacement; the manifest is published last. This is not one multi-file filesystem transaction. Run one instance at a time and use --validate-only after an interrupted run. All prior raw/processed/database/schema files, analytical exports and validation evidence remain unchanged.

## Power BI acceptance boundary

**The CSV analytical handoff is reconciled to the validated prior layers.** The specification, import function and DAX measure definitions are provided for Desktop assembly. No PBIX was created, and DAX/visual interactions/conditional formatting have not been executed in the Power BI engine. The specification includes acceptance checks for types, exact card values, filter scope, zero versus NULL rendering and missing/untranslated categories. Complete these before publishing the report.
