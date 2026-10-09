# Project Scope

**Project:** E-commerce Sales & Customer Analytics  
**Organization:** Riverside Data Analytics LLC  
**Stage:** Validated SQLite, business/customer SQL and dashboard CSV handoff complete; Power BI specification supplied, PBIX assembly pending

## Business objective

Understand sales trends, product performance, customer purchasing behavior,
geographic performance, and retention to support commercial decisions. All
questions and KPIs below are proposed; feasibility and definitions must be
confirmed against the real data before analysis begins.

## Business questions

1. How do sales and order volume change over time, and when are peak periods?
2. Which products and categories contribute most to sales and units sold?
3. How do basket size and average order value vary across customer groups?
4. How much sales activity comes from new customers versus returning customers?
5. Which countries or regions generate the most sales, orders, and customers?
6. How often do customers purchase again, and how does retention vary by cohort?
7. How do cancellations, returns, and discounts affect recorded sales, where these
   fields are available?
8. Which evidence-based opportunities could improve product performance and
   customer retention?

## Data requirements and intake

Preferred fields include order ID, order date, customer ID, product ID/name,
category, quantity, unit price, discounts, order status, refunds/returns, currency,
and country/region. Product cost is optional for profitability analysis.

The dataset may contain order lines, order headers, or separate related tables.
Document the grain and keys before joining tables or calculating totals to avoid
double counting. A stable customer ID is required for customer and retention
metrics; do not substitute names or email addresses without an approved approach.

Before analysis:

- Record the source, permitted use, file format, refresh frequency, and data owner.
- Obtain a data dictionary or confirm field meanings with the source owner.
- Confirm the date range, timezone, currencies, and whether customer purchase
  history predates the extract.
- Review missing values, duplicate keys, invalid dates, inconsistent statuses,
  negative quantities, and potential personal information.
- Agree on eligible order statuses and the treatment of discounts, returns,
  refunds, taxes, and shipping.
- Identify which planned analyses are supported and document exclusions.

## Planned KPIs

These are initial broader definition proposals. The first implemented SQL layer
uses the precise definitions in [kpi_definitions.md](kpi_definitions.md): delivered
orders for observed item sales, all orders for operations, and customer_unique_id
for customer identity. Its AOV excludes freight and is based on observed item sales,
not net revenue. Definitions/results for that layer supersede the corresponding
proposals below; unsupported net-revenue, refund, margin, and retention analyses
remain deferred.

- **Net sales:** Merchandise sales for eligible transactions, less discounts and
  merchandise returns/refunds. Exclude taxes and shipping unless the business
  agrees otherwise. Reconcile source totals and avoid subtracting adjustments
  already included in source amounts. Document whether refunds are assigned to
  the original order date or refund date.
- **Order count:** Distinct eligible order IDs; never count order lines as orders.
- **Average order value (AOV):** Net sales divided by eligible order count, using
  the same period and order population. Define treatment of fully refunded orders.
- **Units sold:** Sum of eligible quantities. Report returned quantities separately
  or deduct them for net units only when the source supports that distinction.
- **Purchasing customers:** Distinct non-null customer IDs with an eligible order
  in the reporting period. Disclose anonymous or missing customer IDs separately.
- **Sales growth:** Percentage change in net sales between comparable, complete
  periods. A zero prior-period value makes percentage growth undefined.
- **Product/category sales share:** Net sales for the product or category divided
  by total net sales for the same reporting population and period.
- **New and returning customers:** New customers have their first observed eligible
  purchase in the period; returning customers purchased before it. These labels
  describe the available history unless full purchase history is confirmed.
- **Repeat purchase rate:** Customers with at least two distinct eligible orders
  in a defined observation window divided by purchasing customers in that window.
  This measure depends on the window length and is separate from cohort retention.
- **Monthly cohort retention:** Customers from a first-observed-purchase month who
  place an eligible order in a later month divided by the original cohort size.
  Mark future and incomplete months as unobserved, not zero retention.
- **Return/refund rate (conditional):** Agree on an order, unit, or monetary basis
  once return/refund fields are understood; clearly label the selected basis.
- **Gross margin (conditional):** Net sales minus attributable cost of goods sold;
  gross margin percentage is gross margin divided by net sales. Requires reliable
  cost and return cost treatment. Do not infer costs from sales prices.

Ratios with zero denominators will be shown as undefined. Do not combine currencies
without an agreed conversion method and rate source. Geography will use a consistent
location field, preferably order shipping location if available; sales totals alone
do not establish regional market penetration.

## Planned analyses

- **Data quality:** Profile coverage, missingness, duplicates, key integrity, and
  reconciliation to source totals after intake.
- **Sales trends:** Compare daily or monthly sales, orders, AOV, and comparable-period
  growth. Evaluate seasonality only if the available history supports it.
- **Product performance:** Rank products/categories by sales and units; examine sales
  concentration, discounts, and returns where supported.
- **Customer behavior:** Examine order frequency, basket size, customer contribution,
  and new versus returning purchasing activity.
- **Geographic performance:** Compare sales, orders, customers, and AOV by available
  country or region, disclosing unknown locations.
- **Retention:** Build monthly first-purchase cohorts, retention rates, and time
  between purchases while accounting for incomplete observation windows.
- **Customer segmentation (conditional):** Use recency, frequency, and monetary value
  if stable customer IDs and sufficient purchase history are available. Document
  the reference date and segmentation rules.

## Expected deliverables

1. **Data documentation:** Source inventory, field dictionary, grain/key definitions,
   quality notes, and finalized KPI definitions in `docs/`.
2. **Reproducible pipeline:** Readable Python scripts in `src/`, SQL schema/queries in
   `sql/`, validated dependency versions, and documented run instructions.
3. **SQLite database and analytical datasets:** Validated staging/relational tables
   in `data/database/olist_analytics.db`; compact first-stage analytical outputs
   in `data/analytics/`, as supported by data.
4. **Exploratory notebooks:** Documented exploration and charts in `notebooks/` after
   the real data is available.
5. **BI dashboard:** A Power BI or Tableau project in `dashboards/` covering supported
   KPIs and analyses, with clear date filters and metric definitions.
6. **Business report:** An executive overview, verified findings, recommendations,
   and limitations in `reports/`, with supporting figures as needed.

## Boundaries and completion criteria

The initial scaffold phase created structure and documentation only. The subsequent
dataset acquisition step downloaded the real Olist dataset; see
[the source record](dataset_source.md). The reproducible CSV cleaning pipeline is now
implemented, with decisions and measured results in
[the cleaning report](../reports/cleaning_report.md). SQLite ingestion and independent
database reconciliation are now complete; see
[the database validation report](../reports/database_validation.md). Business
SQL analysis is now implemented and reconciled in
[the business metric report](../reports/business_metric_validation.md). Read-only
customer value/segmentation/cohort analysis is implemented and independently
reconciled in [customer validation](../reports/customer_analysis_validation.md),
with [methodology](customer_analysis_methodology.md) and
[factual findings](../reports/customer_analysis_findings.md). Sparse frequency
supports four descriptive frequency/value groups rather than conventional RFM.
The [Power BI specification](powerbi_dashboard_spec.md) and
[dashboard-ready data reconciliation](../reports/dashboard_data_validation.md)
are complete. [Final findings](../reports/final_business_findings.md) and
[business recommendations](../reports/business_recommendations.md) link historical
evidence to hypotheses for future tests. Recommendations do not claim causal
effects. Conventional RFM, actual PBIX assembly and dashboard publication remain
pending. Structural profiling
is documented in [the data dictionary](data_dictionary.md) and
[the profile summary](../reports/data_profile.md). Reconciliation differences,
anomaly treatment, finite history and cohort coverage remain documented limits.
Currency semantics remain unresolved; geolocation is
a separate later cleaning task. Predictive
modeling, production deployment, and automated refresh infrastructure are outside
the initial project scope.

The eventual project is complete when the documented pipeline can be rerun from
the original source, outputs reconcile to agreed rules, dashboard and report metrics
agree with SQL outputs, and findings trace back to the real data. Unsupported
questions and data limitations must be disclosed; no results will be invented to
fill gaps.
