# Business Metric Validation

Run (UTC): 2026-10-06T00:47:40+00:00. User reporting timezone: America/New_York.

**PASS: 32 metric checks and five field-level CSV readbacks; zero failures.**

## Scope and exact definitions

Completed-sales metrics include only order_status = delivered. Operational metrics retain all order statuses. Customer metrics use customer_unique_id through the customer_id join. Item sales sum price_hundredths, excluding freight; they do not represent net revenue. AOV is observed item sales / all completed orders, not payments / orders or item-plus-freight / orders. Items sold count item records, because no source quantity column is supplied. Repeat customers have at least two completed orders in the available extract. See docs/kpi_definitions.md for every numerator, denominator, source, exclusion, and limitation.

All money totals and changes remain INTEGER hundredths of unspecified source units. No currency symbol is asserted. Averages, shares, rates, and MoM percentages retain their exact integer numerator/denominator pairs. Six-place Decimal text is display only, rounded half-up, without binary floats. Blank CSV ratios mean undefined; blank category names mean source NULL. No division by zero is coerced to zero.

## Method and preservation

The read-only runner executes every numbered SQL file plus validation.sql under a single read transaction. Every child is independently aggregated to order_id before joining. The validator rereads INTEGER base-table records and recomputes results using independent Python counters, sets, and integer sums; expected results do not come from the business SQL. It checks every order-level aggregate/flag/identity, every category/customer/month/status KPI, all rational components, shared-CTE drift, and saved SQL reconciliations. Export files are reread field by field.

All 25 protected files, including the database, schema.sql, and every raw/processed file, retained identical before/after SHA-256 hashes. Database hash `b5d332fc0edde0d40800a5f5fa65b8f7ebafea7091e65e3bef907d1d6ba5eac7` also matches the prior independent database validation evidence. No table, view, index, data record, or source schema was changed. Geolocation was not loaded or joined.

## Main numerical results

- `completed_orders`: 96,478.
- `distinct_customers`: 93,358.
- `item_sales_hundredths`: 1,322,149,811.
- `freight_hundredths`: 219,827,564.
- `items_sold`: 110,197.
- `payment_total_hundredths`: 1,542,246,177.
- `orders_missing_items`: 0.
- `orders_missing_payments`: 1.
- `orders_missing_reviews`: 646.
- `first_completed_purchase_timestamp`: `2016-09-15 12:16:38`.
- `last_completed_purchase_timestamp`: `2018-08-29 15:00:37`.
- `average_order_value_hundredths`: `13704.158575`.
- `average_items_per_order`: `1.142198`.

Customer overview:

- `unique_customers`: 93,358.
- `customers_one_completed_order`: 90,557.
- `customers_two_plus_completed_orders`: 2,801.
- `completed_orders`: 96,478.
- `item_sales_hundredths`: 1,322,149,811.
- `orders_missing_items`: 0.
- `repeat_customer_rate_percent`: `3.000278`.
- `average_completed_orders_per_customer`: `1.033420`.
- `average_completed_sales_per_customer_hundredths`: `14162.147979`.

All-order status distribution:

- `delivered`: 96,478 orders; 97.020344% of all orders. Missing items/payments/reviews: 0/1/646.
- `shipped`: 1,107 orders; 1.113223% of all orders. Missing items/payments/reviews: 1/0/75.
- `canceled`: 625 orders; 0.628513% of all orders. Missing items/payments/reviews: 164/0/20.
- `unavailable`: 609 orders; 0.612423% of all orders. Missing items/payments/reviews: 603/0/14.
- `invoiced`: 314 orders; 0.315765% of all orders. Missing items/payments/reviews: 2/0/5.
- `processing`: 301 orders; 0.302692% of all orders. Missing items/payments/reviews: 0/0/6.
- `created`: 5 orders; 0.005028% of all orders. Missing items/payments/reviews: 5/0/2.
- `approved`: 2 orders; 0.002011% of all orders. Missing items/payments/reviews: 0/0/0.
- `cancellation_rate_percent`: 0.628513% (all-order denominator).
- `unavailable_order_rate_percent`: 0.612423% (all-order denominator).
- `delivered_order_rate_percent`: 97.020344% (all-order denominator).

Top 10 categories by eligible item sales (all 74 category groups remain in the export):

- 1. `beleza_saude`: 123,313,172 hundredths; 9,465 item records; 8,647 category orders; 9.326717% sales share.
- 2. `relogios_presentes`: 116,617,698 hundredths; 5,859 item records; 5,495 category orders; 8.820309% sales share.
- 3. `cama_mesa_banho`: 102,343,476 hundredths; 10,953 item records; 9,272 category orders; 7.740687% sales share.
- 4. `esporte_lazer`: 95,485,255 hundredths; 8,431 item records; 7,530 category orders; 7.221969% sales share.
- 5. `informatica_acessorios`: 88,872,461 hundredths; 7,644 item records; 6,530 category orders; 6.721815% sales share.
- 6. `moveis_decoracao`: 71,192,769 hundredths; 8,160 item records; 6,307 category orders; 5.384622% sales share.
- 7. `utilidades_domesticas`: 61,562,869 hundredths; 6,795 item records; 5,743 category orders; 4.656270% sales share.
- 8. `cool_stuff`: 61,020,410 hundredths; 3,718 item records; 3,559 category orders; 4.615242% sales share.
- 9. `automotivo`: 57,896,665 hundredths; 4,140 item records; 3,810 category orders; 4.378979% sales share.
- 10. `brinquedos`: 47,128,648 hundredths; 4,030 item records; 3,804 category orders; 3.564547% sales share.

Category order counts overlap and are not additive. Category/customer item sales, category freight/items, and monthly sales/freight/items/order counts all reconcile exactly to the delivered overview. Distinct monthly customers are not additive. No order is multiplied by child joins, including split payments and multiple/reused review IDs.

## Payment-versus-item reconciliation

Difference is **observed payments minus (observed item sales + freight)**: payment_total - (item_sales + freight). It is an audit comparison, not a revenue, discount, refund, or receivables KPI. Missing child rows do not establish zero-valued transactions. Coverage-group contributions below explain the arithmetic using observed totals; only both_present orders support an order-level amount comparison.

### all_orders

- Orders: 99,441.
- Observed item sales + freight: 1,584,355,324 hundredths.
- Observed payments: 1,600,887,212 hundredths.
- Difference: +16,531,888 hundredths.
- `both_present`: 98,665 orders; items+freight 1,584,340,978; payments 1,584,628,017; difference contribution +287,039 hundredths.
- `items_only`: 1 orders; items+freight 14,346; payments 0; difference contribution -14,346 hundredths.
- `payments_only`: 775 orders; items+freight 0; payments 16,259,195; difference contribution +16,259,195 hundredths.
- `neither_present`: 0 orders; items+freight 0; payments 0; difference contribution +0 hundredths.
- Comparable orders matching exactly: 98,089; payment greater: 367; payment smaller: 209.
- Comparable orders differing by exactly one or two hundredths: 309.

### delivered_orders

- Orders: 96,478.
- Observed item sales + freight: 1,541,977,375 hundredths.
- Observed payments: 1,542,246,177 hundredths.
- Difference: +268,802 hundredths.
- `both_present`: 96,477 orders; items+freight 1,541,963,029; payments 1,542,246,177; difference contribution +283,148 hundredths.
- `items_only`: 1 orders; items+freight 14,346; payments 0; difference contribution -14,346 hundredths.
- `payments_only`: 0 orders; items+freight 0; payments 0; difference contribution +0 hundredths.
- `neither_present`: 0 orders; items+freight 0; payments 0; difference contribution +0 hundredths.
- Comparable orders matching exactly: 95,908; payment greater: 362; payment smaller: 207.
- Comparable orders differing by exactly one or two hundredths: 306.

The coverage decomposition reconciles exactly to each aggregate difference. Remaining differences on both-present orders are source discrepancies, not floating-point or join-multiplication errors. Small differences may reflect upstream rounding/recording, but this extract cannot establish the cause. It lacks facts sufficient to attribute differences to discounts, refunds, taxes, or payment timing. No equality was forced and no source amount was altered.

## Coverage and material interpretation limits

- `2016-09`: 4 all orders, 1 delivered; warnings: extract boundary, completed-sales boundary. MoM comparison eligible: 0.
- `2016-11`: 0 all orders, 0 delivered; warnings: no observed orders. MoM comparison eligible: 0.
- `2018-08`: 6,512 all orders, 6,351 delivered; warnings: completed-sales boundary. MoM comparison eligible: 0.
- `2018-09`: 16 all orders, 0 delivered; warnings: no completed orders in the observed snapshot. MoM comparison eligible: 0.
- `2018-10`: 4 all orders, 0 delivered; warnings: extract boundary. MoM comparison eligible: 0.
- The extract's first/last purchase months and first/last completed-sales months are conservatively flagged. Calendar gaps remain explicit. Late periods can have unresolved order outcomes; zero observed completed sales does not prove zero underlying business activity. Interior months are not certified complete, and percentages involving flagged/gap periods are NULL.
- The history is finite: repeat-customer counts describe completed orders observed here, not lifetime repeat behavior. Purchases outside the extract and non-delivered history are excluded.
- `source category NULL` retained: 1,537 eligible item records; 17,072,663 hundredths; 1.291281% of eligible item sales.
- `portateis_cozinha_e_preparadores_de_alimentos` retained: 14 eligible item records; 393,363 hundredths; 0.029752% of eligible item sales.
- `pc_gamer` retained: 8 eligible item records; 130,695 hundredths; 0.009885% of eligible item sales.
- Delivered orders with at least one retained lifecycle anomaly flag: 1,396. Flags overlap; they do not change completed-sales eligibility and no chronology is repaired.
- Delivered review records created before purchase: 6. Review averages in reusable aggregates weight review records equally and retain repeated associations.

Order anomaly/coverage flags (all orders / delivered):

- `flag_approval_before_purchase`: 0 / 0.
- `flag_carrier_before_purchase`: 166 / 165.
- `flag_carrier_before_approval`: 1,359 / 1,350.
- `flag_delivery_before_purchase`: 0 / 0.
- `flag_delivery_before_carrier`: 23 / 23.
- `flag_delivered_missing_order_approved_at`: 14 / 14.
- `flag_delivered_missing_order_delivered_carrier_date`: 2 / 2.
- `flag_delivered_missing_order_delivered_customer_date`: 8 / 8.
- `flag_items_missing`: 775 / 0.
- `flag_payments_missing`: 1 / 1.
- `flag_reviews_missing`: 768 / 646.

Additional item/payment/review flags remain visible by status in order_status_summary.csv. A zero payment remains an observed zero; a missing payment remains absent. Missing lifecycle stages and product metadata are retained and do not trigger deletion.

## Validation checks

- PASS: One order-level row per source order; every aggregate/identity/flag correct.
- PASS: Every order_item_summary group reconciles to independent base records.
- PASS: Every payment_summary group reconciles to independent base records.
- PASS: Every review_summary group reconciles to independent base records.
- PASS: Sales overview: every KPI independently recomputed.
- PASS: Monthly: complete calendar, every KPI/lag/boundary rule.
- PASS: Category: every KPI/rank, NULL and untranslated labels preserved.
- PASS: Customer overview: persistent-ID counts, repeat rate, and all rational components.
- PASS: Operations: every status, rate, missing-child count, and source flag.
- PASS: Saved SQL reconciliation: order-level rows.
- PASS: Saved SQL reconciliation: distinct order-level IDs.
- PASS: Saved SQL reconciliation: item rows.
- PASS: Saved SQL reconciliation: item sales hundredths.
- PASS: Saved SQL reconciliation: freight hundredths.
- PASS: Saved SQL reconciliation: payment rows.
- PASS: Saved SQL reconciliation: payment hundredths.
- PASS: Saved SQL reconciliation: review rows.
- PASS: Saved SQL reconciliation: review score sum.
- PASS: Saved SQL reconciliation: delivered headers.
- PASS: Saved SQL reconciliation: integer monetary storage violations.
- PASS: Monthly totals reconcile: completed_orders.
- PASS: Monthly totals reconcile: item_sales_hundredths.
- PASS: Monthly totals reconcile: freight_hundredths.
- PASS: Monthly totals reconcile: items_sold.
- PASS: Category totals reconcile: item_sales_hundredths.
- PASS: Category totals reconcile: freight_hundredths.
- PASS: Category totals reconcile: items_sold.
- PASS: Customer-level item sales are additive to eligible sales.
- PASS: Completed-order counts agree in sales/customer/operations.
- PASS: Category-order coverage equals eligible orders with items.
- PASS: Payment difference decomposition (all_orders); equality NOT required.
- PASS: Payment difference decomposition (delivered_orders); equality NOT required.
- PASS: five CSV files reread with exact header, row, field, blank-NULL, and ratio-display preservation.
- PASS: every protected input/schema/database hash is unchanged; query and export hashes are recorded in the JSON evidence.

## Exports and reproduction

- `data/analytics/sales_overview.csv`: 1 rows; no customer/order-level export.
- `data/analytics/monthly_sales.csv`: 26 rows; no customer/order-level export.
- `data/analytics/category_performance.csv`: 74 rows; no customer/order-level export.
- `data/analytics/customer_overview.csv`: 1 rows; no customer/order-level export.
- `data/analytics/order_status_summary.csv`: 8 rows; no customer/order-level export.

```powershell
.\.venv\Scripts\python.exe -m src.analysis.run_analysis
.\.venv\Scripts\python.exe -m src.analysis.run_analysis --validate-only
```

The six complete SQL queries run directly in a SQLite client. The shared CTE fragment is copied into them and drift-checked by the runner. To reuse the fragment alone, append a SELECT from the desired aggregate. Export files are staged, read back, and replaced individually; publication across five CSVs and two reports is not one filesystem transaction. Run one analysis instance at a time, and revalidate after an interrupted publication.

## Next-stage readiness

**The outputs are safe for the next analytical stage under the documented eligibility and grain rules.** Counts and monetary rollups reconcile; differences between payments and item-plus-freight totals remain disclosed and require source interpretation. Treat boundary months, late-period outcome coverage, unknown currency semantics, and incomplete customer history explicitly. These metrics are observed item sales, not net revenue or cash-flow reconciliation. No strategic recommendation, visualization, dashboard, RFM segmentation, geolocation analysis, or chronology repair was performed.
