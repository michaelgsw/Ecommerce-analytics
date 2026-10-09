# Customer analysis methodology

## Grain and eligible history

Use only `orders.order_status = 'delivered'`. Join orders to customers by
`customer_id`, then aggregate to `customer_unique_id`. Customer IDs associated
with individual orders are not persistent-person identifiers. The analytical
`customer_level` table is a reusable CTE in
`sql/analysis/customer_level_aggregates.sql`; it is not a persistent database
table. Append `SELECT * FROM customer_level` to that fragment for local exploration.
The runner checks all customer rows without exporting their identifiers.

Items are aggregated by order before customer joins. Customer totals retain all
eligible orders even when an optional child is absent. Observed missing-item
totals contribute no recorded sales/items and keep `orders_missing_items` visible;
absence does not establish a zero-valued transaction. In this extract all delivered
orders have items. Payments and reviews do not determine purchase eligibility.

Item sales sum `price_hundredths`; freight sums `freight_value_hundredths`; item
count counts item records. AOV is customer item sales divided by their completed
order count, excluding freight. These are observed sales, not net revenue or
lifetime value. All sums use integers. Customer-level AOV is exact rational TEXT
plus numerator/denominator columns. Summary ratios include exact integer pairs
and six-place Decimal half-up display text. No currency is asserted.

First/last purchase dates use the naive source purchase timestamp, reduced to
calendar dates. Interval days and recency are calendar-day differences, not elapsed
24-hour durations. Source timestamps have no assigned timezone. Consistent state
means every eligible order-associated customer record has the same usable,
nonblank source state; conflicting or missing assignments remain NULL. This is
customer-record geography, not independently verified delivery location.

## Value distribution and segmentation

The distribution was inspected before choosing the threshold: 90,557 of 93,358
customers have one completed order; customer sales Q1 = 4,765, median = 8,970,
Q3 = 15,475, P90 = 27,999, P95 = 41,986, P99 = 100,499 hundredths.
These percentiles use nearest-rank `ceil(N*p/100)` on ascending customer sales.
Value-distribution bins use observed Q1/median/Q3, keeping equal values together;
they are descriptive bins, not forced segmentation quintiles.

High value means customer item sales **strictly greater than** the Tukey upper
fence `Q3 + 1.5*(Q3-Q1)`, which is 31,540 hundredths here. SQL compares doubled
integer amounts against `2*Q3 + 3*(Q3-Q1)`, preserving even a half-hundredth
threshold without floating-point arithmetic. Values equal to the fence remain
standard. This familiar robust upper-tail rule suits the skewed observed values;
it is not evidence of natural clusters, future loyalty or lifetime value.

Cross the high/standard flag with one completed order versus two or more:
High-value repeat, Standard repeat, High-value one-time, Standard one-time.
Frequency is too sparse to support conventional RFM quintiles in this extract.
The four labels are useful descriptive distinctions. Their separated means are
partly defined by the rule and do not independently validate predictive usefulness.
Sales accumulate over unequal observed tenure; old/new customers are not equally
exposed. The threshold is a reproducible statistic, not a validated business policy.

For Pareto analysis, rank customer sales descending, breaking ties by persistent
ID only for deterministic selection. Top p% selects `ceil(N*p/100)` customers;
the output includes actual count/percentage, total selected sales, cumulative
sales contribution and cutoff value for every p = 1 through 100. The inverse
80% metric finds the smallest integer customer count whose cumulative sales are
at least 80% of total sales. Boundary ties can split an exact-N top group; equal
values contribute equally. IDs are never exported. No 80/20 pattern is assumed.

## Recency

Reference date is **2018-08-29**, the maximum purchase date among observed delivered
orders. It is the latest observed completed-purchase date, not a certified complete
business cutoff. Recency = reference date minus last observed completed purchase
date. Nearest-rank median recency is 218 days. Labels are `recent within observed
period` for recency <= median and `less recent within observed period` otherwise.
Equal recencies stay together; group sizes need not be equal. These labels never
mean currently active/churned customers. Outcome and terminal extract coverage
limit conclusions even at this historical reference date.

## Cohorts and monthly return activity

Assign each customer to the month of their first **observed** completed purchase.
Deduplicate activity to customer/month before joining cohort membership. M1/M2/M3
are calendar months after the acquisition month, not 30/60/90-day windows. Every
rate uses distinct active cohort customers in that target month / original cohort
size. A customer may return in multiple months. Monthly return rates are neither
cumulative repeat rates nor survival probabilities. M0 is cohort membership
(100%), not repeat retention. Any observed repeat rate is 2+ completed orders
anywhere in the history / original cohort size, including acquisition-month and
terminal-month orders.

The retention matrix distinguishes:

- `baseline_membership`: M0. Acquisition month coverage limitations remain flagged
  in the cohort summary even though every observed member is present by definition.
- `interior_observed`: target month has observed orders and precedes the terminal
  completed month. A measured count of zero supports an observed zero rate here;
  completeness is not independently certified.
- `calendar_gap`: no orders of any status observed in the target month (November
  2016 here). Primary counts/rates are NULL; a raw observed zero is not an estimate
  of zero underlying retention.
- `terminal_partial`: August 2018, the last completed purchase month. Primary
  counts/rates are NULL; actual observed customer activity remains separately
  available. The latest delivered purchase is August 29, and late order outcomes
  may be unresolved. No missing-period activity is invented.
- `future_unobserved`: months after August 2018. Observed counts and primary
  counts/rates are NULL, including September/October with no observed delivered
  orders. Later all-status order records do not provide completed-outcome follow-up.

`flag_insufficient_three_month_coverage` means at least one of M1–M3 is not
interior observed. Initial/terminal acquisition cohorts are separately flagged.
M4+ counts distinct customers returning in **any eligible interior month at offset
4 or later**, excluding terminal partial activity; NULL when none is available.
Available future-month counts make unequal follow-up visible. Cohort total sales
and observed repeat rates include all delivered history, whereas primary monthly
retention and M4+ counts use the conservative coverage rule above.

The findings compare pooled M1–M3 over the same cohorts with all three interior
months. Each denominator is the sum of original sizes of that fixed cohort set;
the report does not pool progressively different cohorts into one retention curve.
Older cohorts' full-history repeat rates have longer follow-up and cannot be
ranked as directly comparable customer quality. First observed acquisition can
be left censored; absence of future purchases is right censored.
Very small cohorts produce unstable percentages: September and December 2016
each contain one observed customer. December's 100% M1 rate is one returning
customer, not evidence of typical retention. Retain cohort sizes beside rates.

## Timing and category behavior

Sort each customer's completed orders by purchase timestamp, then order_id.
First-to-second timing includes only customers with 2+ observed completed orders.
Median uses both central observations when count is even; exact rational
components retain half-day medians. Shares within 30/60/90/180 calendar days
include same-day seconds and divide by repeat customers only. They do not estimate
the probability that all customers will repeat and do not adjust for censoring.
Also retain all consecutive-order intervals, with separate scope labels. Their
count equals completed orders minus completed customers.

Identical purchase timestamps are explicitly flagged. ID tie breaking establishes
computational reproducibility, not true purchase order or independent shopping
intent. Same-day intervals can include split/batched purchases.

Aggregate items per order/category before producing category sets or joining
customer groups. Compare first-to-second and all-consecutive pairs separately:
identical known sets, overlapping changed sets, disjoint known sets, or unknown.
Any missing category or itemless order makes a pair unknown, even if some other
categories are known. Each pair receives exactly one class. Category-set equality
ignores category item counts. Distinct customer counts across classes may overlap.
Top categories rank item sales within one-time/repeat customer groups using full
observed-history membership. Category customer/order counts overlap; sales/items
remain additive. Missing categories and absent translations are retained.

## Reproduction and output privacy

```powershell
.\.venv\Scripts\python.exe -m src.analysis.run_customer_analysis
.\.venv\Scripts\python.exe -m src.analysis.run_customer_analysis --validate-only
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The four numbered SQL files 06–09 contain marked, complete SELECT statements,
each with the shared CTE prefix; 08 also appends the cohort CTEs. The runner checks
exact copies for drift. If a shared fragment changes, update every corresponding
complete query. SQLite is read-only with query_only enabled in one read transaction.
The database/schema, all raw/processed files and five prior compact exports are
hash-checked and untouched.

Four requested compact CSVs contain only aggregate data. The wide retention
matrix stores per-offset raw observed count, eligible count/rate and coverage;
`new_customers` is every cell's exact denominator. NULL exports as blank. JSON
evidence additionally retains complete value/frequency/concentration/recency,
timing and category summaries without customer/order IDs, alongside hashes and
independent check results. No final dashboard or strategic recommendations are
produced. Publication replaces files individually; run one instance at a time and
use --validate-only after any interrupted run.
