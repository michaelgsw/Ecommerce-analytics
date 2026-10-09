# KPI Definitions: First SQL Business-Analysis Layer

## Eligibility and scope

Completed-sales metrics use **delivered orders only**. All other statuses are
excluded from those calculations but remain unchanged and available to all-order
operational metrics. No chronology, optional-child, zero-value, missing-category,
or translation anomaly removes an otherwise eligible delivered order.

Customer-level identity is `customer_unique_id`, reached through
`orders.customer_id -> customers.customer_id`. An order-associated customer record
is not a separate persistent customer. This stage contains no RFM, retention cohort,
dashboard, visualization, or strategic recommendation.

## Monetary, ratio, and NULL contracts

All money totals and differences use INTEGER `price_hundredths`,
`freight_value_hundredths`, and `payment_value_hundredths`. Source TEXT money is
never summed or cast to FLOAT. Hundredths are an exact source-unit scale; currency
is not explicitly encoded, so no symbol or currency conversion is asserted.

Ratios export exact INTEGER `*_numerator` and `*_denominator` fields. Monetary
means are in **hundredths per denominator**, which may be fractional. The added
base-name ratio column is Decimal TEXT rounded half-up to six decimal places for
display. This does not replace the exact rational pair. Percentage numerators
already include the factor of 100. Missing/zero denominators produce SQL NULL
or a blank display, never a fabricated zero. CSV blanks also represent NULL
source categories and translations, distinguished by explicit flags.

Child summaries are independently reduced to order_id before joins. Orders remain
one row each. Missing child amounts remain NULL at order grain; aggregate sums
report observed amounts only, with missing counts alongside them. A zero-valued
child is distinct from an absent child. Category order counts and monthly customer
counts are nonadditive.

## Monthly coverage rules

All purchase calendar months from the all-order extract bounds are present.
`flag_extract_boundary_month` marks its first/last month;
`flag_completed_sales_boundary_month` marks the first/last purchase month with an
observed delivered order; `flag_no_observed_orders` marks calendar gaps. These are
conservative warnings, not proof that unflagged months are complete. Late snapshot
months may include unresolved order outcomes. MoM percentages require neither
current nor previous month to carry a warning, plus a positive previous metric.
Absolute integer changes remain visible with flags. Zero observed completed sales
must not be interpreted as confirmed zero commerce.

## Individual KPI definitions


### Completed orders

- Business meaning: Observed completed-order volume.
- Exact numerator: COUNT of eligible order headers.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql.
- Known limitations: One row per order after independent child aggregation. Finite extract; status is the observed snapshot; source timezone is unspecified.

### Distinct completed-order customers

- Business meaning: Persistent customers with an observed completed order.
- Exact numerator: COUNT DISTINCT customer_unique_id through the customer_id join.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql.
- Known limitations: Monthly distinct counts overlap and cannot be summed. Finite extract; status is the observed snapshot; source timezone is unspecified.

### Item sales value

- Business meaning: Observed merchandise item prices, excluding freight.
- Exact numerator: SUM order_items.price_hundredths for eligible orders.
- Exact denominator: None (integer hundredths total).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql; sql/analysis/03_product_performance.sql; sql/analysis/04_customer_overview.sql.
- Known limitations: Not net revenue: no inferred discount, tax, return, refund, or currency adjustment. Missing children are disclosed, not imputed; aggregate totals sum observed values only.

### Freight value

- Business meaning: Observed item freight, kept separate from merchandise sales.
- Exact numerator: SUM order_items.freight_value_hundredths for eligible orders.
- Exact denominator: None (integer hundredths total).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql; sql/analysis/03_product_performance.sql.
- Known limitations: Zero freight remains valid; freight is not merchandise sales and no shipping-revenue semantics are asserted.

### Items sold / average items per order

- Business meaning: Observed item records and average item records per completed order.
- Exact numerator: COUNT of eligible order_items records.
- Exact denominator: None for items sold; ALL eligible order headers for average items per order.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql; sql/analysis/03_product_performance.sql.
- Known limitations: The dataset has no quantity field: one item row is the counting unit; order_item_id is a sequence, not quantity.

### Average order value (AOV)

- Business meaning: Mean observed merchandise item sales per completed order.
- Exact numerator: Eligible item sales hundredths.
- Exact denominator: ALL delivered orders in the same scope, including any without items.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/02_monthly_sales.sql.
- Known limitations: Excludes freight and payments. Not net-sales AOV. A missing-item count is exported; if such orders exist, observed-value coverage is incomplete and the mean is not a verified complete basket value.

### Monthly completed orders, customers, item sales, freight, items, and AOV

- Business meaning: Monthly variants of the preceding KPIs.
- Exact numerator: Same definitions, restricted to purchase timestamp YYYY-MM.
- Exact denominator: Same definitions in that month; AOV denominator is that month's delivered order count.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/02_monthly_sales.sql.
- Known limitations: Calendar spine spans ALL-order extract minimum/maximum months. Includes zero-observation gaps; zero observed sales does not establish no underlying business activity; customer counts are nonadditive.

### MoM completed-order change

- Business meaning: Difference from the previous calendar month.
- Exact numerator: Current completed orders minus previous calendar-month completed orders.
- Exact denominator: None for integer change; prior completed-order count for relative change, numerator multiplied by 100.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions; percentage withheld if either month is a boundary or no-order gap, or prior count is zero/missing.
- SQL source: sql/analysis/02_monthly_sales.sql.
- Known limitations: Integer changes remain visible even when interpretation is flagged. Comparisons never skip a calendar gap. Percentages are conditional observed changes, not certified full-period growth.

### MoM item-sales change

- Business meaning: Change in observed eligible item sales by purchase month.
- Exact numerator: Current item sales hundredths minus previous calendar-month item sales hundredths.
- Exact denominator: None for hundredths change; prior item sales hundredths for relative change, numerator multiplied by 100.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions; percentage withheld if either month is a boundary or no-order gap, or prior sales are zero/missing.
- SQL source: sql/analysis/02_monthly_sales.sql.
- Known limitations: Boundary rules also flag first/last completed-sales months because outcome coverage can end before the all-order extract. Interior completeness is not guaranteed.

### Category item sales / freight / items sold

- Business meaning: Observed eligible item performance grouped by source category.
- Exact numerator: SUM eligible item price / freight hundredths; COUNT eligible item records.
- Exact denominator: None (totals).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: Products with source NULL categories stay in their own NULL group; English remains NULL for untranslated labels. No fabricated labels or translations.

### Completed orders by category

- Business meaning: Eligible orders containing at least one item in a category.
- Exact numerator: COUNT DISTINCT eligible order_id within each category.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: One order can contain multiple categories, so category order counts overlap and are not additive.

### Distinct products sold by category

- Business meaning: Products represented by eligible item records.
- Exact numerator: COUNT DISTINCT product_id within each category.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: Counts product identities, not catalog size, stock, or quantity; no product-name data is invented.

### Average category item price

- Business meaning: Mean observed eligible item price in the category.
- Exact numerator: Category item sales hundredths.
- Exact denominator: Eligible item-record count in the category.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: Weights item records equally. Freight excluded. Retains an exact rational pair and a rounded Decimal display.

### Category share of item sales

- Business meaning: Category contribution to eligible merchandise item sales.
- Exact numerator: 100 times category item sales hundredths.
- Exact denominator: ALL eligible item sales hundredths, including source NULL and untranslated category groups.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: Undefined if the total is zero. Rounded display percentages may not sum to exactly 100; exact integer numerators reconcile.

### Top 10 categories by item sales

- Business meaning: Ten category groups with greatest eligible merchandise sales.
- Exact numerator: ROW_NUMBER ordered by category item sales descending, then source category ascending (NULL first).
- Exact denominator: None; is_top_10 = sales_rank <= 10.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/03_product_performance.sql.
- Known limitations: Returns ALL category groups with ranks and a top-10 flag; no rank filtering removes missing categories. Ties are resolved deterministically by source label.

### Unique completed-order customers

- Business meaning: Persistent customer population for customer-level metrics.
- Exact numerator: COUNT customer_unique_id groups with at least one eligible order.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: customer_id is only the order-associated join key. This is not the full customer table population or lifetime customer base.

### Customers with exactly one completed order

- Business meaning: Observed single-completed-order customer population.
- Exact numerator: COUNT customer_unique_id groups with eligible order count = 1.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: A customer may have other non-delivered or outside-extract purchases; this is not a lifetime first-purchase claim.

### Customers with two or more completed orders

- Business meaning: Observed repeat-completed-order customer population.
- Exact numerator: COUNT customer_unique_id groups with eligible order count >= 2.
- Exact denominator: None (count).
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: Uses persistent identity; all eligible distinct order headers count. Not a retention cohort or RFM segment.

### Repeat customer rate

- Business meaning: Share of observed eligible customers with multiple completed orders.
- Exact numerator: 100 times customers with at least two eligible orders.
- Exact denominator: Unique customer_unique_id groups with at least one eligible order.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: Observed-window repeat rate; purchase history before/after the extract is unknown. Undefined with no eligible customers.

### Average completed orders per customer

- Business meaning: Observed completed-order frequency among eligible customers.
- Exact numerator: Total eligible order headers.
- Exact denominator: Unique eligible customer_unique_id groups.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: Uses the same population as repeat rate; not annualized or lifetime frequency.

### Average completed item sales per customer

- Business meaning: Mean observed merchandise contribution per eligible customer.
- Exact numerator: Total eligible item sales hundredths (after independent order-item aggregation).
- Exact denominator: Unique eligible customer_unique_id groups.
- Included order statuses: delivered only; monthly variants use the order_purchase_timestamp calendar month.
- Excluded records: All non-delivered orders; no additional anomaly-based exclusions.
- SQL source: sql/analysis/04_customer_overview.sql.
- Known limitations: Excludes freight/payments and unobserved refund/discount adjustments; not lifetime value.

### Order status distribution / share

- Business meaning: Observed fulfillment-state composition.
- Exact numerator: COUNT order headers in each source order_status; relative-share numerator is 100 times that count.
- Exact denominator: None for count; ALL order headers for percentage.
- Included order statuses: All eight observed statuses.
- Excluded records: None.
- SQL source: sql/analysis/05_order_operations.sql.
- Known limitations: Snapshot classification, not a transition or eventual-outcome measure; small partial-month statuses are not normalized away.

### Cancellation rate

- Business meaning: Share of orders observed as canceled.
- Exact numerator: 100 times COUNT order headers where order_status = canceled.
- Exact denominator: ALL order headers.
- Included order statuses: All statuses in the denominator; canceled in the numerator.
- Excluded records: None.
- SQL source: sql/analysis/05_order_operations.sql.
- Known limitations: Rates are repeated as scalar columns by status in the compact export; do not sum them. No cancellation reason or eventual status is inferred.

### Unavailable-order rate

- Business meaning: Share observed as unavailable.
- Exact numerator: 100 times COUNT order headers where order_status = unavailable.
- Exact denominator: ALL order headers.
- Included order statuses: All statuses in the denominator; unavailable in the numerator.
- Excluded records: None.
- SQL source: sql/analysis/05_order_operations.sql.
- Known limitations: Rates are repeated as scalar columns by status in the compact export; do not sum them. No cancellation reason or eventual status is inferred.

### Delivered-order rate

- Business meaning: Share observed as delivered.
- Exact numerator: 100 times COUNT order headers where order_status = delivered.
- Exact denominator: ALL order headers.
- Included order statuses: All statuses in the denominator; delivered in the numerator.
- Excluded records: None.
- SQL source: sql/analysis/05_order_operations.sql.
- Known limitations: Rates are repeated as scalar columns by status in the compact export; do not sum them. No cancellation reason or eventual status is inferred.

### Orders missing items

- Business meaning: Coverage of optional items records.
- Exact numerator: COUNT order headers with zero associated items records.
- Exact denominator: None (count).
- Included order statuses: All statuses by operational status; delivered only in sales overview.
- Excluded records: None for operations; non-delivered excluded from the sales variant.
- SQL source: sql/analysis/05_order_operations.sql; sql/analysis/01_sales_overview.sql.
- Known limitations: Absence is not a zero-valued transaction. Counts come from actual child aggregates; existing missing-child flags remain separately visible.

### Orders missing payments

- Business meaning: Coverage of optional payments records.
- Exact numerator: COUNT order headers with zero associated payments records.
- Exact denominator: None (count).
- Included order statuses: All statuses by operational status; delivered only in sales overview.
- Excluded records: None for operations; non-delivered excluded from the sales variant.
- SQL source: sql/analysis/05_order_operations.sql; sql/analysis/01_sales_overview.sql.
- Known limitations: Absence is not a zero-valued transaction. Counts come from actual child aggregates; existing missing-child flags remain separately visible.

### Orders missing reviews

- Business meaning: Coverage of optional reviews records.
- Exact numerator: COUNT order headers with zero associated reviews records.
- Exact denominator: None (count).
- Included order statuses: All statuses by operational status; delivered only in sales overview.
- Excluded records: None for operations; non-delivered excluded from the sales variant.
- SQL source: sql/analysis/05_order_operations.sql; sql/analysis/01_sales_overview.sql.
- Known limitations: Absence is not a zero-valued transaction. Counts come from actual child aggregates; existing missing-child flags remain separately visible.

### Source anomaly/coverage flag counts

- Business meaning: Visibility of retained lifecycle, metadata coverage, payment, review, and shipment issues.
- Exact numerator: SUM each order flag at order grain; SUM each child flag first within its child table/order, then by source status.
- Exact denominator: None (record counts).
- Included order statuses: All statuses, with delivered subset disclosed in validation.
- Excluded records: None; no chronology repairs or guesses.
- SQL source: sql/analysis/05_order_operations.sql.
- Known limitations: Flags overlap; order flags count orders while child flags count child records. Do not sum them as distinct affected orders; flag meanings remain in cleaning_report.md.

### Observed payment totals and comparison to item sales plus freight

- Business meaning: Audit of observed monetary representations; not a completed-sales revenue KPI.
- Exact numerator: SUM payments.payment_value_hundredths independently by order; difference = observed payments - (observed item sales + freight).
- Exact denominator: None (integer hundredths); both-present comparison restricts to orders with item AND payment records.
- Included order statuses: Delivered and all-order scopes reported separately.
- Excluded records: No source rows removed; compare both-present separately from items-only/payments-only/neither.
- SQL source: sql/analysis/01_sales_overview.sql; sql/analysis/validation.sql; src/analysis/validate_metrics.py.
- Known limitations: Do not force equality. Missing records are unknown, not invented zeros. Differences are decomposed by coverage, and source causes are not recoverable from these fields.

### Reusable average review score

- Business meaning: Mean score over review records attached to an order.
- Exact numerator: SUM review_score independently within reviews for order_id.
- Exact denominator: Review record count for that order.
- Included order statuses: All statuses in reusable summaries; no reviews discarded.
- Excluded records: None; NULL average if an order has no review records.
- SQL source: sql/analysis/order_level_aggregates.sql.
- Known limitations: Exact rational TEXT score_total/review_count, not binary float. Weights each review association equally, including multiple/reused IDs; not a unique-customer sentiment KPI.

## Reproduction and safe use

Run `.\.venv\Scripts\python.exe -m src.analysis.run_analysis` from the project root.
The five numbered SQL files are complete standalone queries. Their shared CTEs
must remain identical to order_level_aggregates.sql; the runner checks that contract.
The independent report records every reconciliation and payment difference.
Use `--validate-only` to check existing exports without replacing them.

Aggregate output definitions supersede the corresponding preliminary proposals in
project_scope.md for this first analytical stage. Net revenue, discounts, returns,
margins, customer lifetime value, full monthly coverage, and currency semantics
are not established by this layer.

## Customer value, segmentation and cohort extension

The [customer analysis methodology](customer_analysis_methodology.md) extends
these definitions for SQL files 06–09: persistent-customer analytical grain,
customer sales/AOV, observed frequency, exact Pareto concentration, Tukey upper-tail
segments, historical median-based recency, first-observed completed-purchase
cohorts, fixed cohort retention denominators/coverage, conditional repeat intervals
and order-category set comparisons. Delivered eligibility and exact item-sales
semantics remain identical to the validated first layer. Cohort monthly activity
and any observed repeat rate have different observation bases; unknown future
rates are never zero. These extension definitions supersede preliminary RFM
proposals for the current stage.
