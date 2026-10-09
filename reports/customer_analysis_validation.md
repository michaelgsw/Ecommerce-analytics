# Customer Analysis Validation

Run (UTC): 2026-10-06T01:28:22+00:00.

**PASS: 28 independent checks and four exact CSV readbacks; zero failures.**

## Scope and methods

All customer behavior uses delivered orders, with customer_id only bridging orders to customer_unique_id. The reusable customer_level CTE is the analytical table: one row per persistent customer. It remains read-only and is not materialized into the database. It includes first/last purchase dates, order/item counts, exact item sales/freight, exact AOV numerator/denominator and rational text, first-to-last calendar days, repeat flag, consistent state, observation date, recency, missing-item/state flags, and cohort month.

Items are aggregated per order before customer joins; customer-month activity is deduplicated before cohort joins; category activity is aggregated per order/category before customer joins. Repeat transitions have exactly one row per consecutive order pair. Independent expected results are rebuilt from base tables using Python integer sums, sets, counters, datetime parsing and sorting, without analytical SQL/CTEs. Every customer field and classification, every summary metric, all 100 Pareto cutoffs, and every cohort cell are checked, including types and NULL positions.

All monetary sums remain INTEGER hundredths of unspecified source units. Ratios retain integer numerator/denominator pairs; display uses six-place Decimal half-up text. The wide retention matrix preserves exact counts and its original cohort denominator in new_customers. No binary floating-point amount is accepted. Timestamp ordering uses the unmodified naive source timestamps, with order_id as a deterministic tie breaker. Date intervals count calendar days; no source timezone is assigned.

## Reconciliation

- Customer rows: 93,358, each with a distinct customer_unique_id.
- Completed orders: 96,478; sum of customer, segment and cohort order counts.
- Item sales: 1,322,149,811 hundredths; exact customer, segment, cohort and category sums.
- Repeat customers: 2,801; equals the prior validated result.
- Consecutive repeat pairs: 3,120; orders minus customers.
- Unassigned customer states: 37; inconsistent/missing states stay NULL.

## Retention denominators and missing observation

Every M1/M2/M3/later-month rate divides distinct customers returning in that specific calendar month by the original first-observed-completed-purchase cohort size. This is monthly return activity, not survival, cumulative repeat, or order count. Customers may return in several months; these numerators cannot be added as distinct customers. Month 0 is 100% cohort membership, not repeat retention. Observed repeat rate uses customers with at least two completed orders anywhere in the available history / original cohort size, including same-month and terminal-month orders.

For primary retention rates, target months after August 2018 are future_unobserved, August 2018 is terminal_partial, and November 2016 is calendar_gap. Their returning counts/rates are NULL (blank CSV fields). Actual observed terminal-month activity is retained separately in observed_customers. The gap's observed zero only describes the extract; it is not a zero-retention estimate. Interior observed months permit descriptive rates but are not certified complete. M4+ counts distinct customers over eligible interior offsets >=4, excludes terminal partial activity, and is NULL when none of these months is available. Cohort repeat totals have a broader observation basis than these conservative retention rates. First/terminal cohorts and insufficient first-three-month coverage are flagged.

## Checks

- PASS: Customer-level rows: one per persistent ID; every date/state/value/recency field.
- PASS: Every customer's frequency/value/neutral-recency assignment.
- PASS: Prior independently validated customers.
- PASS: Prior independently validated repeat customers.
- PASS: Prior independently validated completed orders.
- PASS: Prior independently validated eligible item sales hundredths.
- PASS: Full frequency distribution.
- PASS: Value distribution with unsplit quartile ties.
- PASS: Quantiles, exact mean/fence and median recency.
- PASS: One-time versus repeat customers: every mean and sales share.
- PASS: Every segment count/value/frequency/recency/state field.
- PASS: Neutral historical recency groups.
- PASS: Every Pareto 1%-100% cutoff and cumulative sale.
- PASS: Actual customers required for 80% sales.
- PASS: Every cohort count/value, fixed denominator and exposure flag.
- PASS: Every retention cell: customer/month uniqueness; future/gap/partial NULLs.
- PASS: First-to-second timing: exact median and conditional day-window shares.
- PASS: Both first-to-second and all-consecutive interval distributions.
- PASS: Category comparisons: one row per pair; NULLs unknown; every behavior share.
- PASS: Order/category aggregation: every one-time/repeat category count/sale/rank.
- PASS: segments: customers additive.
- PASS: segments: orders additive.
- PASS: segments: INTEGER item sales additive.
- PASS: cohorts: customers additive.
- PASS: cohorts: orders additive.
- PASS: cohorts: INTEGER item sales additive.
- PASS: All consecutive repeat joins have exactly orders minus customers rows.
- PASS: Category group item sales reconcile to eligible total.
- PASS: four saved CSVs reread with identical headers, rows, fields, blanks and Decimal displays.
- PASS: all 30 protected database/schema/raw/processed/prior-export files retain identical SHA-256 hashes.
- PASS: database hash matches independent database evidence; five prior export hashes match prior metric evidence.

## Outputs and reproduction

- data/analytics/customer_segments.csv: 4 aggregate rows.
- data/analytics/customer_cohort_summary.csv: 23 aggregate rows.
- data/analytics/cohort_retention_matrix.csv: 23 aggregate rows.
- data/analytics/repeat_purchase_summary.csv: 9 aggregate rows.

No customer/order identifiers appear in exports or the aggregate JSON evidence. JSON retains every aggregate result (including full concentration, interval and category distributions), query/input/export hashes and check outcomes.

```powershell
.\.venv\Scripts\python.exe -m src.analysis.run_customer_analysis
.\.venv\Scripts\python.exe -m src.analysis.run_customer_analysis --validate-only
```

Each numbered SQL file contains complete, separately marked SELECT statements. Shared CTE copies are drift-checked. CSVs are staged/read back and replaced individually; CSV/report publication is not a single filesystem transaction. Run one instance at a time and revalidate after interrupted publication.

**These results are reconciled and usable for descriptive customer analysis under the documented definitions.** Boundary coverage, finite customer history, tied timestamps, unknown categories, state ambiguity and monetary semantics remain interpretation limits. See customer_analysis_methodology.md and the findings report.
