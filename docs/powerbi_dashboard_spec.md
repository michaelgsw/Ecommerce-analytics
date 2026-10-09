# Power BI dashboard specification

**Project:** Riverside Data Analytics LLC — E-commerce Sales & Customer Analytics.
This is a four-page report specification and validated CSV handoff. Build the PBIX
in Power BI Desktop using the supplied Power Query function and measure catalog.
No PBIX or published report has been created in this stage.

## Definitions and reporting scope

Completed behavior uses delivered orders only. Operational status metrics use all
99,441 orders. Persistent customers use customer_unique_id through the customer_id
bridge in upstream SQL; dashboard exports contain no customer/order identifiers.
Completed history is 2016-09-15 through 2018-08-29. The all-order monthly table
extends through October 2018. These are observed historical outcomes, not current
activity or complete lifetime history. Source event timestamps have no assigned
timezone. Retention offsets and repeat intervals use calendar months/days.

Item sales exclude freight. AOV = item sales / completed orders. Customer mean
sales = item sales / completed customers. Counts and sums retain their validated
integer values. Dashboard money displays in **source units**, dividing hundredths
by 100 for presentation only. Use no currency symbol: currency semantics remain
unconfirmed. Observed item sales are not net revenue, profit or reconciled cash.
All percent numerators in CSV already include the factor 100; DAX divides by
100 again to obtain a fraction before applying percentage format.

Authoritative definitions: [KPI definitions](kpi_definitions.md) and
[customer methodology](customer_analysis_methodology.md). Preparation makes no
eligibility, threshold, numerator or denominator changes.

## Data tables and model

Import only the nine CSVs from `data/dashboard/`, with their exact filename stems
as table/query names. `dashboard_manifest.json` is the type/hash contract read by
the import function, not a tenth fact table.

- `dashboard_kpis`: 7 rows, one per metric_key. Full-history KPI rational components,
  population, unit, source display text and population-specific period labels.
  Completed dates are NULL for operational cards, whose observed months extend
  through October 2018; no delivered-only cutoff is assigned to all-order metrics.
- `dashboard_monthly_sales`: 26 rows, one per purchase month. Monthly completed
  sales/orders and distinct customers; all-order counts; AOV/MoM components and
  original flags. `chart_item_sales_hundredths` is a display-only series with NULL
  for gaps and post-completed-window unresolved outcomes. Original observed sales
  and coverage flags remain available.
- `dashboard_customer_segments`: 4 mutually exclusive segment rows. Counts,
  sales, AOV/customer-mean components, full-population share denominators, threshold,
  reference date, customer_type and the high-value one-time highlight flag.
- `dashboard_customer_concentration`: 100 cumulative Pareto points plus one inverse
  80%-sales threshold record. Points are cumulative, not additive. Separate
  record_type filters are mandatory.
- `dashboard_cohorts`: 552 rows, one per cohort_month/month_index. Original cohort
  size, observed and rate-eligible activity, exact retention components, coverage,
  target month and acquisition-cohort flags. Sum cohort size at M0 only.
- `dashboard_repeat_timing`: 9 summary metrics plus 14 interval-bin rows. Summary
  day windows overlap; bins within each scope do not. Keep record_type/scope
  filters explicit. Median and window shares apply only to observed repeat customers.
- `dashboard_categories`: 218 rows, one per customer_type/category_key. Scope is
  `All completed`, `One-time`, or `Repeat`. All completed sales duplicate the
  combined customer-type sales: never add these scopes together. Category
  customers/orders overlap and are not additive across categories. Source category
  NULL and absent English translation remain NULL, with separate flags/display labels.
- `dashboard_category_transition`: 4 first-to-second transition classes; 2,801 pairs
  in total. Every pair is in exactly one class. Customer counts and timestamp ties
  are retained for interpretation.
- `dashboard_order_status`: 8 all-status rows; counts, fixed all-order share
  components and missing-child counts. These are operational metrics.

**Keep all nine aggregate tables disconnected.** Create no relationships between
them and disable automatic relationship detection. Shared labels do not imply
compatible fact grains. The current exports lack month/category/segment joint
distributions and cannot support unrestricted cross filtering. Do not attempt
bidirectional, many-to-many or fact-to-fact relationships to simulate missing data.

All counts, totals, flags, ranks, offsets and rational components import as Whole
number (Int64). Date fields import as Date; labels/month keys/display_value_text
remain Text. Preserve blanks as null. Six-place source KPI display text is
authoritative for audit; DAX ratio values are presentation calculations. Do not
load integer monetary totals as Decimal number or Fixed decimal, and do not
round source components. Power BI's Whole number type preserves integer storage;
Decimal number is approximate and Fixed decimal retains only four fractional
digits. [Microsoft data type documentation](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-data-types).

## Slicers and visual interaction contract

Use local slicers with visible scope labels. Do not sync them across pages. Set
each slicer's interactions explicitly using Format > Edit interactions, choosing
Filter for listed target visuals and None for all others. Also set chart-to-chart
interactions to None unless a safe interaction is explicitly listed below.
[Microsoft interaction documentation](https://learn.microsoft.com/en-us/power-bi/create-reports/service-reports-visual-interactions).

- **Purchase month:** `dashboard_monthly_sales[month]`, Page 1. Filter only the
  monthly trend and its coverage table. Label “Purchase month — monthly visuals
  only.” Full-history KPI cards, categories and status distribution stay unchanged.
  Never sum monthly distinct customers to obtain selected-period unique customers.
- **Product category:** `dashboard_categories[category_display]`, Pages 1 and 4
  independently. Filter only category visuals on that page. Sales shares retain
  their full-population/customer-type denominators under category selection.
  Page 1 Top 10 ranks are fixed full-history ranks; selecting a lower-ranked category
  can leave that visual empty. State this beside the selector. Page 4's complete
  category table provides all categories without a Top N restriction.
- **Customer segment:** `dashboard_customer_segments[segment]`, Page 2. Filter the
  segment comparison, customer-type charts and mean-sales/AOV comparison. Global
  concentration and the fixed high-value one-time highlight stay unchanged and
  carry “Full observed history” labels. No segment filter is supported for category
  mixes, cohort rates or timing because those joint aggregates were not exported.
- **Customer type:** `dashboard_customer_segments[customer_type]`, Page 2, with
  the same safe targets as segment. On Page 4 use a separate
  `dashboard_categories[customer_type]` slicer, allowing only One-time/Repeat and
  filtering only category mix. Keep overall category performance and transitions
  unchanged. Do not sync these slicers: they come from different disconnected tables.
- **Acquisition cohort:** `dashboard_cohorts[cohort_month]`, Page 3. Filter cohort
  size, M1–M3 cards, eligible-cohort counter and heatmap. It does not filter the
  full-history repeat timing visuals. This is acquisition month, not purchase month.

Shares stay relative to full validated denominators after subset selection;
subtotals need not equal 100%. Selected segment means/AOV use sums of their
numerators divided by sums of their matching denominators, never a mean of means.
All page headers state “Historical extract; filters apply only to labeled visuals.”

Tooltip aggregation follows the same grain as its visual: SUM only additive
numerators/counts, MAX for repeated full-population denominators, SELECTEDVALUE
for a single source row's labels/flags. Use exact rational pairs. Do not let
Power BI sum repeated denominators, cumulative points or category order counts.
Each fixed card also gets its explicit visual-level source-record filter so
raw tooltip fields refer to that card's metric, not other rows in the same table.

## Page 1 — Executive Overview

Layout: completed-sales cards across the top; a clearly separated operational
card beside them; monthly trend below; category and operational status comparisons
at the bottom. Use restrained teal for completed sales and neutral gray for
operational metrics. Footer explains monetary scale and extract coverage.

### E1. Completed-sales KPI cards

- Chart type: Five separate Card visuals, one per named measure.
- Data source: dashboard_kpis.
- X-axis/Y-axis/legend: none; card value is each named measure.
- Filters: each measure locks its metric_key and full-history scope; also set the
  matching visual-level metric_key filter (completed_orders, unique_completed_customers,
  observed_item_sales, average_order_value, repeat_customer_rate); no slicer interactions.
- Tooltip fields: numerator, denominator, population, unit, completed-window dates.
- Titles/measures: “Completed orders” / Completed Orders; “Unique completed customers” /
  Unique Completed Customers; “Observed item sales (source units)” / Observed Item
  Sales (source units); “AOV excluding freight (source units)” / Average Order Value
  (source units); “Observed repeat customer rate” / Observed Repeat Customer Rate.
- Business question: What completed sales and customer behavior were observed over
  the full available history?

### E2. All-order operational card

- Chart type: Card; value Delivered Order Rate, with All Observed Orders as supporting value.
- Data source: dashboard_kpis.
- X-axis/Y-axis/legend: none.
- Filters: full-history, all-order denominator; visual-level metric_key =
  delivered_order_rate; no slicer interactions.
- Tooltip fields: delivered count 96,478, all-order count 99,441, population,
  metric_window_start_month/metric_window_end_month (September 2016–October 2018).
- Title: “Delivered order rate — all observed orders.”
- Business question: What fraction of all recorded orders has delivered status?

### E3. Monthly completed-sales trend

- Chart type: Clustered column chart; use categorical month axis and show all months.
- Data source: dashboard_monthly_sales.
- X-axis: month, chronologically sorted by month_date.
- Y-axis: Monthly Chart Sales (source units).
- Legend: none.
- Filters: purchase-month slicer only; preserve all coverage states in the dataset.
- Tooltip fields: raw item_sales_hundredths, completed_orders, distinct_customers
  (“monthly distinct”), Monthly AOV (source units), coverage_status and all source flags.
- Title: “Monthly observed item sales — delivered orders.”
- Business question: How did observed completed sales vary by purchase month?

Gaps and post-August unresolved completed outcomes have blank chart values. The
separate original observed totals remain auditable. Display boundary observed
bars with a note; do not infer completeness or seasonality from them.

### E4. Monthly coverage detail

- Chart type: Table.
- Data source: dashboard_monthly_sales.
- X-axis/Y-axis/legend: not applicable; columns month, coverage_status, all_orders,
  completed_orders, raw item_sales_hundredths and flag_mom_comparable.
- Filters: purchase-month slicer only.
- Tooltip fields: first/last boundary flags, gap flag, original MoM components.
- Title: “Monthly coverage and observed totals.”
- Business question: Which trend periods are gaps, boundaries or unresolved outcomes?

### E5. Top categories by completed item sales

- Chart type: Horizontal bar chart.
- Data source: dashboard_categories.
- X-axis: Category Sales (source units).
- Y-axis: category_display, sorted by descending sales.
- Legend: none.
- Filters: customer_type = All completed; sales_rank <= 10; local category slicer only.
- Tooltip fields: raw/English labels, Category Sales Share, Category Order Count,
  items_sold, sales_rank, missing/translation flags.
- Title: “Top 10 categories — full-history delivered item sales.”
- Business question: Which categories contributed the most recorded merchandise sales?

### E6. Operational order-status distribution

- Chart type: Horizontal bar chart.
- Data source: dashboard_order_status.
- X-axis: Status Order Count.
- Y-axis: order_status.
- Legend: none.
- Filters: none; fixed all-order population; no chart/slicer cross interactions.
- Tooltip fields: Status Share of All Orders, orders_missing_items/payments/reviews,
  status_share_percent_denominator.
- Title: “Order status distribution — all observed orders.”
- Business question: How are all recorded orders distributed across lifecycle statuses?

## Page 2 — Customer Value & Segmentation

Layout: customer-type comparisons left; concentration right; segment table and
fixed high-value one-time highlight beneath. Subtitle: “Delivered purchases;
segments describe observed value and frequency; not a predictive customer model.”

### V1. One-time versus repeat customer counts

- Chart type: Column chart.
- Data source: dashboard_customer_segments.
- X-axis: customer_type.
- Y-axis: Segment Customers.
- Legend: none.
- Filters: local customer-type and segment slicers.
- Tooltip fields: Segment Customer Share, completed_orders, numerator/denominator components.
- Title: “Observed customers by purchase type.”
- Business question: How many customers have one versus multiple completed orders?

### V2. Sales contribution by customer type

- Chart type: Horizontal bar chart; show share labels alongside source-unit sales.
- Data source: dashboard_customer_segments.
- X-axis: Segment Sales (source units).
- Y-axis: customer_type.
- Legend: none.
- Filters: local type/segment slicers; full-population share denominator stays fixed.
- Tooltip fields: Segment Sales Share, Segment Customers, completed_orders,
  raw item_sales_hundredths, sales_share_percent_denominator.
- Title: “Observed item sales by customer type.”
- Business question: What share of all observed item sales came from each purchase type?

### V3. Customer sales and order-value comparison

- Chart type: Clustered column chart.
- Data source: dashboard_customer_segments.
- X-axis: customer_type.
- Y-axis: Average Customer Sales (source units), Segment AOV (source units).
- Legend: measure names (“Sales per customer”, “Sales per completed order”).
- Filters: local type/segment slicers.
- Tooltip fields: respective numerator/denominator pairs, customers and completed_orders.
- Title: “Sales per customer and AOV — matching weighted denominators.”
- Business question: Does higher customer sales reflect more orders or larger observed orders?

### V4. Cumulative customer sales concentration

- Chart type: Line chart (100 precomputed points).
- Data source: dashboard_customer_concentration.
- X-axis: target_customer_percent, sorted ascending; label “Target top customer percentile
  (ceil N*p/100)”; numeric labels are 1–100, not a percentage-formatted fraction.
- Y-axis: Pareto Sales Share, percentage axis 0–100%.
- Legend: none.
- Filters: record_type = pareto_point; no segment/type/category/month interaction.
- Tooltip fields: Pareto Customer Share (actual selected fraction), customers_selected,
  item_sales_hundredths, cutoff_customer_sales_hundredths and both exact ratio pairs.
- Title: “Cumulative item sales by top customers — full observed history.”
- Business question: How concentrated are sales without assuming an 80/20 rule?

### V5. Top 1%, 5%, 10%, 20% contributions

- Chart type: Column chart with four points; supporting card for the inverse 80% threshold.
- Data source: dashboard_customer_concentration.
- X-axis: target_customer_percent (top groups).
- Y-axis: Pareto Sales Share; supporting cards Customers Needed for 80% Sales and
  Customer Share Needed for 80% Sales.
- Legend: none.
- Filters: chart record_type = pareto_point, highlight_top_group = 1; inverse cards lock
  sales_80_threshold; no cross interactions. Do not add the four cumulative shares.
- Tooltip fields: selected count, actual customer fraction, cumulative sales amount/denominator.
- Title: “Top customer groups' contribution — full observed history.”
- Business question: What do the common top-group cutoffs contribute, and how many
  customers actually produce 80% of sales?

### V6. Four-segment comparison

- Chart type: Table with a teal accent for highlight_high_value_one_time = 1.
- Data source: dashboard_customer_segments.
- X-axis/Y-axis/legend: not applicable; rows segment, columns Segment Customers,
  Segment Customer Share, Segment Sales (source units), Segment Sales Share,
  Average Customer Sales (source units), Segment AOV (source units).
- Filters: local type/segment slicers.
- Tooltip fields: completed_orders, exact threshold numerator/denominator, observation_date.
- Title: “Observed frequency and value segments.”
- Business question: How do mutually exclusive customer groups differ in recorded contribution?

### V7. High-value one-time highlight

- Chart type: Two cards plus explanatory text.
- Data source: dashboard_customer_segments.
- X-axis/Y-axis/legend: none.
- Filters: named measures High Value One-Time Customers and High Value One-Time Sales
  Share lock the full-history segment; also filter the visuals to segment =
  High-value one-time; no slicer interactions.
- Tooltip fields: 456,987,318 item-sales hundredths; 7.599777% full-population customer share.
- Title: “High-value one-time — full observed history.”
- Business question: How large is this descriptive upper-value group and its contribution?

Visible note: “High value = observed customer item sales > 31,540 hundredths
(315.40 source units), using Q3 + 1.5 IQR. Statistical upper tail; predictive
usefulness untested. Customer tenure differs. Historical recency reference:
2018-08-29; these labels do not imply currently active/churned customers.”

## Page 3 — Retention & Cohorts

Layout: acquisition-size plot and M1–M3 cards top; heatmap central; repeat timing
below in a separate full-history area. Heatmap/card populations and timing
populations must be labeled separately.

### R1. Acquisition cohort sizes

- Chart type: Column chart.
- Data source: dashboard_cohorts.
- X-axis: cohort_month, sorted by cohort_date.
- Y-axis: New Cohort Customers (M0 only).
- Legend: none.
- Filters: acquisition-cohort slicer only; visual-level month_index = 0.
- Tooltip fields: initial/terminal cohort flags, insufficient-three-month-coverage flag.
- Title: “First observed completed-purchase cohorts.”
- Business question: How many observed customers entered each acquisition cohort?

### R2. Comparable M1/M2/M3 return cards

- Chart type: Three separate cards; supporting eligible-cohort/customer count and coverage note.
- Data source: dashboard_cohorts.
- X-axis/Y-axis/legend: none.
- Filters: named measures M1 Return Rate, M2 Return Rate, M3 Return Rate keep only
  cohorts with flag_insufficient_three_month_coverage = 0, target interior observation.
  Acquisition-cohort selection may narrow this fixed common-coverage population.
  Apply the same filters at visual level, plus month_index = 1/2/3 on its respective
  card, so returning-count tooltips have exactly the same eligible records.
- Tooltip fields: eligible three-month cohorts/customers and summed returning counts.
- Title: “Monthly return rates — same cohorts with observed M1–M3 coverage.”
- Business question: How does later-month return activity compare for the same cohort population?

Unfiltered denominator: 68,618 original customers in 17 cohorts for every card.
Values: M1 331/68,618, M2 240/68,618, M3 180/68,618. If selection contains no
eligible cohorts, show BLANK and “No selected cohorts have common M1–M3 coverage.”
The heatmap still displays any individually eligible selected-cohort cells; cards
use the stricter common-three-month rule. Never average cohort percentages.

### R3. Coverage-aware cohort heatmap

- Chart type: Matrix with text values and conditional background colors.
- Data source: dashboard_cohorts.
- X-axis/columns: month_index ascending, M0–M23; label “Calendar months after acquisition.”
- Y-axis/rows: cohort_month ascending.
- Values: Cohort Cell Text; color field Cohort Cell Background.
- Legend: “M0 = membership; FU = future unobserved; CG = calendar gap; TP = terminal
  partial; numeric 0.00% = measured interior zero.” Color supports these text labels.
- Filters: acquisition-cohort slicer only. Keep all cells; do not filter out NULL
  primary rate rows. Disable row/column subtotals and grand totals.
- Tooltip fields: coverage_status, target_month, observed_customers,
  returning_customers_for_rate, new_customers, exact retention components and flags.
- Title: “Monthly observed return activity — original cohort denominators.”
- Business question: When do cohort members return, and which cells lack comparable observation?

Background colors: FU gray #E5E7EB; CG pale yellow #FFF2CC; TP pale purple #EDE4F7;
M0 pale blue #DCE6F1; measured zero pale green #F3FAF5; positive return activity
progressively darker green. Dark text throughout. Use the Field value conditional
format option on Cohort Cell Text, based on Cohort Cell Background. Text labels
keep undefined cells visible even when the numeric rate is BLANK. Validate their
appearance in the Desktop engine. [Microsoft conditional-format documentation](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-conditional-table-formatting).

### R4. Median first-to-second interval

- Chart type: Card; Median Days to Second Purchase.
- Data source: dashboard_repeat_timing.
- X-axis/Y-axis/legend: none.
- Filters: measure locks summary / median_days_to_second_purchase; no cohort interactions.
- Tooltip fields: count = 2,801, numerator = 29, denominator = 1; same-day count = 829;
  first/second timestamp ties = 253.
- Title: “Median days to second purchase — observed repeat customers.”
- Business question: What is the median calendar interval among customers who were
  observed to purchase twice?

### R5. Repeat timing windows

- Chart type: Column chart; four separate cumulative thresholds, not stacked shares.
- Data source: dashboard_repeat_timing.
- X-axis: metric, sorted by sort_order (30, 60, 90, 180).
- Y-axis: Repeat Window Share.
- Legend: none.
- Filters: record_type = summary; metric in within_30_days, within_60_days,
  within_90_days, within_180_days; scope = first_to_second; no cohort interactions.
- Tooltip fields: count, numerator, denominator = 2,801, unit, scope.
- Title: “First-to-second timing — share of observed repeat customers.”
- Business question: What fraction of observed repeat customers returned within each day window?

### R6. Repeat interval distribution

- Chart type: Column chart, mutually exclusive bins.
- Data source: dashboard_repeat_timing.
- X-axis: metric/interval-bin label, sorted by sort_order.
- Y-axis: Repeat Interval Count.
- Legend: none.
- Filters: record_type = interval_bin; scope = first_to_second; no cohort interactions.
  An optional local scope selector may switch this chart alone to all_consecutive,
  with a dynamic title and denominator; it does not change the median/window cards.
- Tooltip fields: min_days, max_days, count, denominator, scope.
- Title: “First-to-second interval distribution — calendar days.”
- Business question: How do observed repeat intervals distribute across disjoint day bins?

Visible note: “Monthly returns are not lifetime retention. Initial/terminal
cohorts, the November 2016 gap and incomplete follow-up limit comparisons.
August 2018 primary rates are blank; observed activity remains in tooltips.
Tiny cohort percentages are unstable. Timing shares condition on observed repeat
customers, include same-day seconds, and do not estimate all-customer repeat
probability. Tied timestamps have no known true sequence.”

## Page 4 — Product & Category Performance

Layout: all-completed category performance left; customer-type category mix right;
category continuity below. This page uses category-level facts. No unsupported
individual-product ranking is implied by its page name.

### P1. Complete category performance

- Chart type: Table with data bars on sales; preserve all 74 overall category groups.
- Data source: dashboard_categories.
- X-axis/Y-axis/legend: not applicable; category_display rows; columns Category Sales
  (source units), Category Sales Share, Category Order Count, items_sold and raw/English labels.
- Filters: customer_type = All completed; category slicer only; no customer-type slicer interaction.
- Tooltip fields: flags, raw item_sales_hundredths, sales_rank, full sales-share denominator.
- Title: “Category sales and orders — delivered purchases.”
- Business question: What contribution and recorded order coverage does each category have?

Do not sum category order/customer counts or category scopes. The supplied order
measure suppresses a multiple-category total. Use source labels as the stable
display dimension; English translations remain an optional separate column.

### P2. One-time versus repeat category mix

- Chart type: Clustered horizontal bar chart; all categories available, with scroll
  or local category selection to focus the view.
- Data source: dashboard_categories.
- X-axis: Category Sales Share (full customer-type denominator).
- Y-axis: category_display.
- Legend: customer_type (One-time, Repeat).
- Filters: customer_type in One-time/Repeat; category and local customer-type slicers only.
- Tooltip fields: Category Sales (source units), Category Order Count, Category
  Customer Count, full group denominator, sales_rank and missing/translation flags.
- Title: “Category mix within one-time and repeat customer sales.”
- Business question: Which categories contribute to each observed purchase group's sales?

Type membership uses full observed history. A category filter does not reset the
group denominator, so selected categories can contribute less than 100%. Category
order/customer counts are category memberships, not exclusive category segments.

### P3. First-to-second category continuity

- Chart type: Horizontal bar chart; four exhaustive transition classes.
- Data source: dashboard_category_transition.
- X-axis: First-to-Second Transition Share.
- Y-axis: behavior_display, sorted by sort_order.
- Legend: none.
- Filters: first_to_second scope is already the export's only scope; no category,
  type, segment, cohort or month slicer interactions.
- Tooltip fields: order_transitions, distinct_customers, tied_timestamp_transitions,
  exact share components, scope.
- Title: “First-to-second category continuity — observed repeat customers.”
- Business question: Do successive observed purchases keep the same category set,
  change with some overlap, move to disjoint sets or lack usable categories?

Unknown means at least one category is missing or an order has no recorded items.
Missing labels are not forced into same/different groups. A partially overlapping
category set is distinct from an identical set or no overlap. Movement does not
prove recommendation effectiveness, affinity or shopping intent.

## Exact Desktop build steps

1. From the project root in PowerShell, run the builder and then saved-file validation:

   ```powershell
   .\.venv\Scripts\python.exe -m src.dashboard.build_dashboard_data
   .\.venv\Scripts\python.exe -m src.dashboard.build_dashboard_data --validate-only
   ```

2. Open Power BI Desktop and create a blank report. In File > Options and settings >
   Options, under Current File > Data Load, disable automatic relationship detection
   and automatic date/time (Time intelligence section) for this file. The exact pane
   layout can vary by release. See [relationship options](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-create-and-manage-relationships)
   and [auto date/time options](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-auto-date-time).
3. Home > Transform data opens Power Query. Manage Parameters > New Parameter:
   name `DashboardFolder`, type Text, required, current value:

   ```text
   C:\path\to\riverside-ecommerce-analytics\data\dashboard
   ```

   Replace this placeholder with the absolute path to your own local
   `data/dashboard/` folder before loading or refreshing data.

4. New Source > Blank Query. Rename it `DashboardCsv`. Open Advanced Editor and
   paste the entire function from `dashboards/powerbi_import.pq`. It reads CSV in
   UTF-8, verifies manifest headers, converts empty fields to null and assigns exact
   types. Text/CSV is a supported Power Query connector; explicit types avoid
   reliance on automatic inference. [Microsoft CSV connector documentation](https://learn.microsoft.com/en-us/power-query/connectors/text-csv).
5. Create nine more blank queries. Name each exactly as its CSV stem, open Advanced
   Editor and enter its corresponding function call, for example:

   ```powerquery
   DashboardCsv("dashboard_kpis")
   ```

   Repeat for dashboard_monthly_sales, dashboard_customer_segments,
   dashboard_customer_concentration, dashboard_cohorts, dashboard_repeat_timing,
   dashboard_categories, dashboard_category_transition and dashboard_order_status.
   Enable load for these nine tables only. Do not import the parameter, function
   or manifest as data tables. Remove any extra automatically inserted Changed Type
   step. Confirm Whole number/Text/Date types and blank/null cells in the preview.
6. Close & Apply. In Model view verify all nine tables are disconnected; delete
   any auto-created relationship. Do not introduce a common calendar/category
   relationship across incompatible aggregate facts. Set raw means, ratios, ranks,
   flags and source labels to Don't summarize where appropriate; use explicit measures.
7. Use Modeling > New measure. Paste one complete named declaration at a time from
   `dashboards/powerbi_measures.dax`, excluding comment lines if desired. Create
   measures in catalog order so dependencies exist. The file is a measure catalog,
   not one DAX query. DIVIDE without an alternate value returns BLANK for a zero
   denominator; do not substitute zero. [Microsoft DIVIDE documentation](https://learn.microsoft.com/en-us/dax/divide-function-dax).
8. Format count measures as `#,##0`; source-unit monetary measures as `#,##0.00`,
   no currency symbol; day measures as `0.0`; rate/share measures as `0.00%` (use
   `0.000%` for pooled small cohort return cards). Raw exported percent text must
   never be percentage-formatted numerically without division by 100. Hide audit
   components from routine field browsing only after all acceptance checks pass.
9. Create/rename four report pages exactly as specified. Use a 16:9 canvas with
   readable text, a clear header, sufficient space around dense cohort/category
   visuals and a visible definition/limitation footer. Add each named visual with
   the fields, measures and explicit visual-level filters above. Sort months/cohorts
   by Date columns, transition labels and interval bins by sort_order.
10. Add the scoped slicers. Format > Edit interactions: set each intended target to
    Filter and every other visual to None. Turn off unlisted chart cross interactions
    and slicer sync. Record full-history versus filtered scope visibly beside cards.
11. For the heatmap use Cohort Cell Text in Values. Disable all totals/subtotals.
    Apply background-color conditional formatting, Format style = Field value,
    based on Cohort Cell Background. Keep FU/CG/TP and M0 legend visible. Verify
    measured zero renders as `0.00%`, not an unavailable marker. Add coverage/rate
    counts and denominators to tooltips; retain all M0–M23 columns.
12. Run the acceptance checks below. Save locally as
    `dashboards/riverside_ecommerce_analytics.pbix` when satisfied. Publishing and
    Service refresh configuration are separate later actions. To refresh this
    historical handoff, rerun the builder, validate, then Home > Refresh in Desktop.
    The folder parameter makes moving the project explicit; it does not provide
    automatic live data access or a scheduled refresh.

## Required acceptance checks before publication

- Unfiltered cards: 96,478 completed orders; 93,358 unique completed customers;
  13,221,498.11 source-unit item sales; AOV 137.04158575 source units (display
  137.04); repeat rate 3.000278%; delivered rate 97.020344%; all orders 99,441.
  Exact AOV is 1,322,149,811 / 96,478 hundredths; displayed decimals are rounded.
- Page 2: one-time 90,557, repeat 2,801; repeat sales 72,840,875 hundredths,
  5.509275% of total. Mean customer sales 137.95829544 versus 260.05310603 source
  units (six-place hundredths displays divided by 100); their AOVs differ.
- Fixed highlight: 7,095 high-value one-time customers; 7.599777% customer share;
  34.563959% sales share. Selecting a standard segment changes supported charts
  but leaves this explicitly full-history highlight and concentration unchanged.
- Top 1/5/10/20 sales shares: 11.465666% / 29.129771% / 41.099916% / 56.621700%.
  80% threshold: 42,009 customers, 44.997751% of customers, 80.000214% sales.
- Unfiltered common-cohort cards: 17 cohorts, denominator 68,618; M1 331 returns
  (0.482381%), M2 240 (0.349762%), M3 180 (0.262322%). Selecting only August 2018
  gives no eligible common-three-month cards, while M0 membership stays visible.
- Inspect four heatmap cells: 2016-09/M1 = 0.00% measured zero; 2016-09/M2 = CG;
  2018-06/M2 = TP (16 actual observed customers in the source tooltip); 2018-08/M1
  = FU. Verify their distinct text/backgrounds. M0 is membership, never a repeat rate.
- Timing median 29 days; 30/60/90/180 shares 50.553374% / 61.121028% /
  68.118529% / 82.863263%, denominator 2,801. Cohort selection must not change these.
- Category table has 74 overall groups, including source NULL and two untranslated
  labels. First-to-second counts: same set 1,261, overlapping change 36, no overlap
  1,435, unknown 69; sum 2,801. Selecting a category leaves overall denominator and
  transition chart unchanged. With only health_beauty selected, overall category
  share remains 9.326717%, not 100%.
- Selecting purchase month changes only trend/coverage visuals. Fixed unique
  customer/repeat cards do not pretend to represent the selected month.
- Disable invalid totals: cumulative Pareto points, category order/customer totals,
  mixed category scopes and retention matrix totals. Preserve blank versus zero.

Dataset reconciliation is automated in
[dashboard validation](../reports/dashboard_data_validation.md). The supplied M
function, DAX catalog, formatting and interactions require the Desktop acceptance
checks above; they have not been executed in the Power BI engine in this stage.
