# Final business findings

Scope: the validated historical Olist extract. Completed behavior includes only
delivered orders, using persistent customer_unique_id through the customer_id
bridge. There are 96,478 completed orders, 93,358 completed customers and
1,322,149,811 observed item-sales hundredths (13,221,498.11 source units).
Money excludes freight and unsupported refund/profit adjustments; currency is
not asserted. Six-place ratio displays are rounded, with exact components retained.

Sources: [business validation](business_metric_validation.md),
[customer findings](customer_analysis_findings.md),
[customer validation](customer_analysis_validation.md), and their aggregate JSON
evidence. The [dashboard validation](dashboard_data_validation.md) reconciles the
handoff without redefining any metric.

## 1. Observed repeat purchasing is rare

- Metric: 2,801 / 93,358 customers have 2+ completed orders = **3.000278%**.
- Supporting comparison: 90,557 customers have exactly one completed order
  (96.999722%). Of the repeat customers, 2,573 have exactly two orders; only 228
  have three or more.
- Business interpretation: the observed population is dominated by one-time
  purchases and offers limited frequency variation for conventional RFM quintiles.
  Acquisition and observed repeat behavior describe different parts of customer activity.
- Limitation: finite, unequal follow-up does not establish lifetime purchasing or
  churn. Late acquisitions have less opportunity to repeat, and some multiple
  orders share a calendar date or exact timestamp.

## 2. Repeat customers have higher cumulative sales, with lower AOV

- Metric: repeat customer mean sales = 72,840,875 / 2,801 =
  **26,005.310603 hundredths**, versus 1,249,308,936 / 90,557 =
  **13,795.829544 hundredths** for one-time customers.
- Supporting comparison: repeat customers account for **5.509275%** of item sales,
  versus 3.000278% of customers. Their AOV is 72,840,875 / 5,921 =
  **12,302.123797 hundredths**, compared with 13,795.829544 for one-time customers.
- Business interpretation: higher customer-level contribution accompanies more
  observed orders; it does not arise from a higher average recorded order value.
- Limitation: group membership uses full observed history. These associations
  cannot demonstrate that a retention intervention would cause additional purchases,
  and do not measure net contribution or lifetime value.

## 3. High-value one-time customers contribute a disproportionate share

- Metric: **7,095 customers**, 7.599777% of all completed customers, contribute
  **456,987,318 hundredths**, **34.563959%** of observed item sales.
- Supporting comparison: standard one-time customers number 83,462 (89.399944%
  of customers) and contribute 59.926766% of item sales. All observed repeat
  customers together contribute 5.509275%.
- Business interpretation: the descriptive high-value one-time group has a
  materially larger recorded sales contribution than its customer-count share.
- Limitation: high value is strictly above the empirical Tukey upper fence,
  Q3 + 1.5 IQR = **31,540 hundredths**; it is an upper-tail rule, not a predictive
  model or evidence of customer loyalty. Sales accumulate over differing tenure.
  Separating group means is partly a consequence of the threshold itself.

## 4. Sales concentration differs from an 80/20 pattern

- Metric: top 20% selects 18,672 customers and contributes 748,623,706 hundredths,
  **56.621700%** of sales.
- Supporting comparison: top 1%, 5% and 10% contribute **11.465666%**,
  **29.129771%** and **41.099916%**. The smallest group reaching 80% contains
  **42,009 customers**, **44.997751%** of customers, producing 1,057,722,676
  hundredths (80.000214% of sales).
- Business interpretation: contributions are concentrated, but a literal 80/20
  description overstates the concentration in this extract.
- Limitation: top p% uses ceil(N*p/100) and deterministic tie ordering. Points are
  cumulative, not additive, and describe historical item sales rather than profit,
  payments, lifetime value or future customer potential.

## 5. Observed second purchases often occur quickly

- Metric: median first-to-second interval among **2,801 observed repeat customers**
  is **29 calendar days**.
- Supporting comparison: first seconds within 30/60/90/180 days number
  1,416 / 1,712 / 1,908 / 2,321, with the same denominator 2,801:
  **50.553374% / 61.121028% / 68.118529% / 82.863263%**.
  **829** seconds are same-day (29.596573%), including **253** first/second exact
  timestamp ties. All consecutive intervals total 3,120, rather than 2,801.
- Business interpretation: fast recorded seconds, including same-day orders,
  materially shape the timing distribution among observed repeat purchasers.
- Limitation: these are conditional shares, not the chance that all customers
  repeat within a given window. They do not adjust for censoring. Same-day/tied
  orders may reflect split or batched purchases; true shopping intent and tied
  order sequence cannot be established.

## 6. Later-month cohort return activity is low under common coverage

- Metric: among the **same 17 acquisition cohorts** with interior observation at
  M1, M2 and M3, original cohort sizes sum to **68,618**. Returning customers are
  **331**, **240** and **180**: **0.482381%**, **0.349762%** and **0.262322%**.
- Supporting comparison: 1,168 customers repeat within their acquisition month,
  which does not count as a return in a later calendar month. Six of 23 cohorts
  lack full first-three-month interior coverage. The 552-cell matrix has 231
  interior observed cells, 274 future-unobserved cells, 22 terminal-partial cells,
  two calendar-gap cells and 23 M0 membership cells.
- Business interpretation: observed return activity in later months is low for
  the common covered population. Overall repeat rate and month-specific cohort
  returns measure different behaviors and observation windows.
- Limitation: these are monthly activity rates, not survival probabilities or
  lifetime retention. The first observed purchase may not be first-ever purchase.
  November 2016 has an extract gap; August 2018 is terminal partial. Primary
  future/gap/partial rates are NULL. Interior completeness is not certified.
  Tiny cohorts are unstable: December 2016's 100% M1 rate represents one customer.

## 7. Cross-category and same-set repeat purchases both occur

- Metric: among 2,801 first-to-second pairs, **1,435** have no category overlap
  (**51.231703%**), **1,261** have the same known category set (**45.019636%**),
  **36** have overlapping changed sets (**1.285255%**), and **69** are unknown
  (**2.463406%**).
- Supporting comparison: across 3,120 consecutive pairs, the corresponding
  disjoint/same/overlapping/unknown counts are 1,595 / 1,395 / 47 / 83
  (51.121795% / 44.711538% / 1.506410% / 2.660256%).
- Business interpretation: both category continuity and movement appear in the
  observed repeat history. No-overlap transitions are more common than identical
  sets in both pair populations.
- Limitation: categories are order-level sets, not exclusive item segments; any
  missing category makes a pair unknown. Timestamp ties limit sequence interpretation.
  Transition patterns do not prove affinity, intent or recommendation effectiveness.

## 8. Customer-type category mixes differ

- Metric: the largest one-time category is `beleza_saude`, contributing
  **117,866,842 hundredths**, **9.434563%** of one-time sales. The largest repeat
  category is `cama_mesa_banho`, contributing **9,483,843 hundredths**,
  **13.019947%** of repeat sales.
- Supporting comparison: `beleza_saude` contributes 7.477024% of repeat sales;
  `cama_mesa_banho` contributes 7.432880% of one-time sales. Overall `beleza_saude`
  leads at 123,313,172 hundredths, 9.326717% of all delivered item sales.
- Business interpretation: the observed customer groups have different category
  contribution mixes; rankings describe associations with full-history membership.
- Limitation: different group denominators and product/customer exposure limit
  direct comparisons. These mixes do not isolate the category of the second
  purchase or establish category-driven retention. Missing category sales are
  retained: 17,072,663 hundredths, 1.291281% of overall sales. Two source labels
  have no English translation; none is invented.

## Visible reporting limits

Use historical reference date 2018-08-29 for recency; do not say currently active
or churned. Keep completed-sales and all-order operational populations separate.
Display original cohort sizes, conditional timing denominators and coverage
labels. Keep future/gap/partial cells distinct from measured zero and M0 membership.
Source payment-versus-item differences remain unresolved; delivered payment
totals exceed item-plus-freight totals by 268,802 hundredths, with missing-record
coverage contributing to that reconciliation. Customer-state conflicts leave
37 customer-level states unassigned. Geolocation is not joined. The disconnected
dashboard model intentionally supports scoped filters rather than fabricating
unavailable cross-grain slices.
