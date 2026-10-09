# Independent Olist Validation Report

**Validation date:** October 5, 2026 (America/New_York).

## Scope and method

All nine raw CSVs and all eight prepared CSVs were read directly in the project's
Python 3.12 virtual environment. Checks do not import or call any cleaning/profiling
functions, rerun the pipeline, or rely on its success assertions. Strings and postal
prefixes remain text. Decimal checks use Python Decimal; timestamp checks use the
standard-library datetime parser and an explicit source format. Temporary joins and
comparisons exist only in memory. Only this report is published; no data is changed.

Numbers labeled **raw / processed** report both files in that order. Missing means
empty or whitespace-only. Duplicate count means excess occurrences after the first
unless explicitly labeled repeated distinct values or rows in repeated groups.

Classifications:

- **OK:** Check passes with no detected integrity violation.
- **Expected:** A documented table grain, optional field, or design choice explains it.
- **Needs Investigation:** Source ambiguity/anomaly needs interpretation; retain evidence.
- **Error:** A confirmed key, parse, numeric-domain, preservation, or mapping failure.

## Row counts and duplicate rows

- **OK:** `olist_customers_dataset.csv` → `customers_clean.csv`: 99,441 / 99,441 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_orders_dataset.csv` → `orders_clean.csv`: 99,441 / 99,441 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_order_items_dataset.csv` → `order_items_clean.csv`: 112,650 / 112,650 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_products_dataset.csv` → `products_clean.csv`: 32,951 / 32,951 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_order_payments_dataset.csv` → `payments_clean.csv`: 103,886 / 103,886 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_order_reviews_dataset.csv` → `reviews_clean.csv`: 99,224 / 99,224 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `olist_sellers_dataset.csv` → `sellers_clean.csv`: 3,095 / 3,095 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **OK:** `product_category_name_translation.csv` → `category_translation_clean.csv`: 71 / 71 rows; exact duplicate excess rows 0 / 0. Difference: 0.
- **Expected:** `olist_geolocation_dataset.csv`: raw 1,000,163 rows, 261,831 identical excess rows; no prepared geolocation table exists. Geographic cleaning was explicitly deferred.
- **Expected:** The raw ZIP, `.gitkeep`, profiling JSON, cleaning manifest, and execution log are artifacts/metadata, not CSV tables; row counts do not apply to them.

## Orders

- **OK:** Total rows: 99,441 / 99,441; unique `order_id`: 99,441 / 99,441; duplicate `order_id` excess rows: 0 / 0; missing `customer_id`: 0 / 0.
- **OK:** Unrecognized/blank processed order statuses: 0. Distribution unchanged: True.
- **OK:** Order status `approved`: 2 / 2.
- **OK:** Order status `canceled`: 625 / 625.
- **OK:** Order status `created`: 5 / 5.
- **OK:** Order status `delivered`: 96,478 / 96,478.
- **OK:** Order status `invoiced`: 314 / 314.
- **OK:** Order status `processing`: 301 / 301.
- **OK:** Order status `shipped`: 1,107 / 1,107.
- **OK:** Order status `unavailable`: 609 / 609.

## Customers

- **OK:** Unique `customer_id`: 99,441 / 99,441; duplicate excess rows: 0 / 0; missing persistent identifiers: 0 / 0.
- **Expected:** Unique `customer_unique_id`: 96,096 / 96,096; distinct persistent IDs appearing more than once: 2,997 / 2,997. `customer_id` identifies each order-associated record; `customer_unique_id` links records for the same anonymized customer. Repetition is valid and must be preserved.
- **OK:** Persistent customer-ID frequency distribution exactly preserved: True.

## Order items

- **OK:** Total rows: 112,650 / 112,650; distinct `order_id`: 98,666 / 98,666.
- **OK:** `price` negative: 0 / 0; malformed, nonfinite, or missing combined: 0 / 0.
- **OK:** Zero `price`: 0 / 0. No zero-priced items were found.
- **OK:** `freight_value` negative: 0 / 0; malformed, nonfinite, or missing combined: 0 / 0.
- **Expected:** Zero `freight_value`: 383 / 383. Zero freight is allowed; it does not establish an invalid record.
- **OK:** Missing `product_id`: 0 / 0.
- **OK:** Missing `seller_id`: 0 / 0.

## Products and English category translation

- **Needs Investigation:** Missing product categories: 610 / 610. Source omission remains unknown; products were retained without inventing categories.
- **OK:** Duplicate `product_id` excess rows: 0 / 0.
- **OK:** Supplied English lookup mappings preserved after label normalization: True; raw mappings 71, processed mappings 71.
- **Expected:** English category text was NOT physically merged into `products_clean.csv`. The pipeline deliberately retains a separate normalized translation table and a missing-translation flag. There is no completed English product-column merge to certify.
- **OK:** Independent in-memory left join returns 32,951 rows for 32,951 products, with 32,328 supplied English translations, 610 missing source categories, and 13 untranslated populated categories. No row multiplication or row loss.
- **Needs Investigation:** Untranslated populated product labels: `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`. Keep source labels and nullable English values; do not invent translations.

## Payments

- **Expected:** Orders with multiple payment records: 2,961 / 2,961; distinct payment order IDs: 99,440 / 99,440. Split methods/vouchers can produce multiple records; use `(order_id, payment_sequential)` as the key.
- **OK:** Invalid payment values (missing, malformed, nonfinite, or negative): 0 / 0; negative specifically: 0 / 0.
- **Needs Investigation:** Zero payment amounts: 9 / 9; zero installments: 2 / 2. These are retained edge cases, not automatically invalid decimal values.
- **OK:** Missing payment `order_id`: 0 / 0.

## Reviews

- **Expected:** Duplicate `review_id` excess rows: 814 / 814; distinct repeated `review_id` values: 789 / 789; rows belonging to repeated-ID groups: 1,603 / 1,603. A repeated review ID alone is not a duplicate review/order record.
- **Expected:** Orders with multiple review records: 547 / 547. Preserve the composite `(review_id, order_id)` key.
- **OK:** Missing review scores: 0 / 0.
- **OK:** Malformed/out-of-range populated review scores: 0 / 0.
- **OK:** Review score `1`: 11,424 / 11,424.
- **OK:** Review score `2`: 3,151 / 3,151.
- **OK:** Review score `3`: 8,179 / 8,179.
- **OK:** Review score `4`: 19,142 / 19,142.
- **OK:** Review score `5`: 57,328 / 57,328.

## Required keys and foreign-key integrity

- **OK:** Duplicate key `customers(customer_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `orders(order_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `order_items(order_id, order_item_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `products(product_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `payments(order_id, payment_sequential)`: 0 / 0 excess rows.
- **OK:** Duplicate key `reviews(review_id, order_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `sellers(seller_id)`: 0 / 0 excess rows.
- **OK:** Duplicate key `category_translation(product_category_name)`: 0 / 0 excess rows.
- **OK:** `orders.customer_id` absent from `customers.customer_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** `order_items.order_id` absent from `orders.order_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** `order_items.product_id` absent from `products.product_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** `order_items.seller_id` absent from `sellers.seller_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** `payments.order_id` absent from `orders.order_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** `reviews.order_id` absent from `orders.order_id`: 0 / 0 rows; 0 / 0 distinct keys. Missing fields are checked separately, not counted as orphans.
- **OK:** Customer/order ID sets exactly match: True; processed order-associated customer IDs are unique: True.

## Date ranges, missing values, and malformed timestamps

- **OK:** `orders.order_purchase_timestamp`: raw 2016-09-04 21:15:19 → 2018-10-17 17:30:18; processed 2016-09-04 21:15:19 → 2018-10-17 17:30:18; malformed 0 / 0; ranges/missing counts unchanged: True.
- **OK:** `orders.order_purchase_timestamp` missing: 0 / 0.
- **OK:** `orders.order_approved_at`: raw 2016-09-15 12:16:38 → 2018-09-03 17:40:06; processed 2016-09-15 12:16:38 → 2018-09-03 17:40:06; malformed 0 / 0; ranges/missing counts unchanged: True.
- **Expected:** `orders.order_approved_at` missing: 160 / 160. Lifecycle stage may not have occurred; delivered-status exceptions are checked separately below.
- **OK:** `orders.order_delivered_carrier_date`: raw 2016-10-08 10:34:01 → 2018-09-11 19:48:28; processed 2016-10-08 10:34:01 → 2018-09-11 19:48:28; malformed 0 / 0; ranges/missing counts unchanged: True.
- **Expected:** `orders.order_delivered_carrier_date` missing: 1,783 / 1,783. Lifecycle stage may not have occurred; delivered-status exceptions are checked separately below.
- **OK:** `orders.order_delivered_customer_date`: raw 2016-10-11 13:46:32 → 2018-10-17 13:22:46; processed 2016-10-11 13:46:32 → 2018-10-17 13:22:46; malformed 0 / 0; ranges/missing counts unchanged: True.
- **Expected:** `orders.order_delivered_customer_date` missing: 2,965 / 2,965. Lifecycle stage may not have occurred; delivered-status exceptions are checked separately below.
- **OK:** `orders.order_estimated_delivery_date`: raw 2016-09-30 00:00:00 → 2018-11-12 00:00:00; processed 2016-09-30 00:00:00 → 2018-11-12 00:00:00; malformed 0 / 0; ranges/missing counts unchanged: True.
- **OK:** `orders.order_estimated_delivery_date` missing: 0 / 0.
- **OK:** `order_items.shipping_limit_date`: raw 2016-09-19 00:15:34 → 2020-04-09 22:35:08; processed 2016-09-19 00:15:34 → 2020-04-09 22:35:08; malformed 0 / 0; ranges/missing counts unchanged: True.
- **OK:** `order_items.shipping_limit_date` missing: 0 / 0.
- **OK:** `reviews.review_creation_date`: raw 2016-10-02 00:00:00 → 2018-08-31 00:00:00; processed 2016-10-02 00:00:00 → 2018-08-31 00:00:00; malformed 0 / 0; ranges/missing counts unchanged: True.
- **OK:** `reviews.review_creation_date` missing: 0 / 0.
- **OK:** `reviews.review_answer_timestamp`: raw 2016-10-07 18:32:28 → 2018-10-29 12:27:35; processed 2016-10-07 18:32:28 → 2018-10-29 12:27:35; malformed 0 / 0; ranges/missing counts unchanged: True.
- **OK:** `reviews.review_answer_timestamp` missing: 0 / 0.
- **Expected:** Customers, products, payments, sellers, category translations, and geolocation have no source date/time columns. Do not invent event dates or assume a timezone.

## Chronological relationships and coverage gaps

- **OK:** Approval before purchase: 0 / 0 conflicting rows among 99,281 / 99,281 comparable records. Rows with missing events are excluded from comparison.
- **Needs Investigation:** Carrier handoff before purchase: 166 / 166 conflicting rows among 97,658 / 97,658 comparable records. Rows with missing events are excluded from comparison.
- **Needs Investigation:** Carrier handoff before approval: 1,359 / 1,359 conflicting rows among 97,644 / 97,644 comparable records. Rows with missing events are excluded from comparison.
- **OK:** Customer delivery before purchase: 0 / 0 conflicting rows among 96,476 / 96,476 comparable records. Rows with missing events are excluded from comparison.
- **Needs Investigation:** Customer delivery before carrier handoff: 23 / 23 conflicting rows among 96,475 / 96,475 comparable records. Rows with missing events are excluded from comparison.
- **OK:** Estimated delivery before purchase: 0 / 0 conflicting rows among 99,441 / 99,441 comparable records. Rows with missing events are excluded from comparison.
- **Needs Investigation:** Delivered orders missing `order_approved_at`: 14 / 14; retain missing values and investigate the source status/event discrepancy.
- **Needs Investigation:** Delivered orders missing `order_delivered_carrier_date`: 2 / 2; retain missing values and investigate the source status/event discrepancy.
- **Needs Investigation:** Delivered orders missing `order_delivered_customer_date`: 8 / 8; retain missing values and investigate the source status/event discrepancy.
- **OK:** Shipment deadline before purchase: 0 / 0.
- **Needs Investigation:** Shipment deadlines beyond the latest observed purchase year: 4 / 4. Outside observed coverage is a review heuristic, not proof the deadline itself is impossible.
- **Needs Investigation:** Review creation before purchase: 74 / 74; earlier calendar date 64 / 64; same-day timestamp 10 / 10. Same-day timing can reflect source precision; causes remain unconfirmed.
- **OK:** Review response before review creation: 0 / 0.
- **Expected:** Chronology rule counts overlap. Do not sum them as distinct affected orders, correct dates by guessing, or reject all flagged orders. Flags preserve evidence for later metric-specific treatment.
- **Expected:** Orders without `order_items` records: 775 / 775. Absence of optional child records is distinct from an orphan foreign key.
- **Needs Investigation:** Orders without `payments` records: 1 / 1. Absence of optional child records is distinct from an orphan foreign key.
- **Expected:** Orders without `reviews` records: 768 / 768. Absence of optional child records is distinct from an orphan foreign key.

## Independent source preservation and output provenance

- **OK:** `customers` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `customers` identifier/postal-field changes by source record: 0.
- **OK:** `orders` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `orders` identifier/postal-field changes by source record: 0.
- **OK:** `order_items` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `order_items` identifier/postal-field changes by source record: 0.
- **OK:** `products` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `products` identifier/postal-field changes by source record: 0.
- **OK:** `payments` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `payments` identifier/postal-field changes by source record: 0.
- **OK:** `reviews` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `reviews` identifier/postal-field changes by source record: 0.
- **OK:** Populated review title/message changes, including whitespace and multiline text: 0.
- **OK:** `sellers` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `sellers` identifier/postal-field changes by source record: 0.
- **OK:** `category_translation` source record numbers are valid and unique: True; source filename preserved: True.
- **OK:** `category_translation` identifier/postal-field changes by source record: 0.
- **OK:** Original ZIP SHA-256 matches the download record: True. Current SHA-256: `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`.
- **OK:** Raw `olist_customers_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2`.
- **OK:** Raw `olist_orders_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf`.
- **OK:** Raw `olist_order_items_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279`.
- **OK:** Raw `olist_products_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc`.
- **OK:** Raw `olist_order_payments_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `4f713964f2815dbbaa40b9488268c55aac3627bfce5aa96cf58d1f3616de3cc0`.
- **OK:** Raw `olist_order_reviews_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `012b61c7593e34f51fa614efdf802b9c7056ce6aae5307ddb93236e7cfc797d7`.
- **OK:** Raw `olist_sellers_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e`.
- **OK:** Raw `product_category_name_translation.csv` matches its original ZIP entry byte for byte: True; SHA-256 `a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278`.
- **OK:** Raw `olist_geolocation_dataset.csv` matches its original ZIP entry byte for byte: True; SHA-256 `b514f6fc991b9566aeba02aa5d67e2c3630f034b60a0e05aa0d082a3b66d88d6`.
- **OK:** `customers_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `orders_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `order_items_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `products_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `payments_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `reviews_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `sellers_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** `category_translation_clean.csv` current bytes match the completed cleaning run's manifest: True. This is an artifact check only; all metrics above were recomputed independently.
- **OK:** All files under `data/raw/` AND `data/processed/` have identical before/after SHA-256 hashes: True. Raw CSVs and ZIP also match their download baselines, not merely this validation's starting state.

## Overall classification and SQLite readiness

- **OK:** 107 individually classified findings.
- **Expected:** 15 individually classified findings.
- **Needs Investigation:** 12 individually classified findings.
- **Error:** 0 individually classified findings.

### What should be fixed or resolved before building SQLite?

No confirmed structural, malformed-date, negative-money, required-key, source
preservation, or required-foreign-key error was detected. The files can enter a
lossless staging database without inventing source repairs. Before creating the
constrained prepared schema, apply these documented design requirements:

1. Use unique order_id/customer_id/product_id/seller_id and the validated composite
   item, payment, and review keys. Never use review_id alone as a primary key or
   customer_unique_id to collapse order-associated customer records.
2. Convert nullable empty CSV fields to SQL NULL. Retain postal prefixes/IDs as
   TEXT, parse dates explicitly, preserve unknown timezone, and preserve decimal
   amounts exactly. Decide monetary storage and confirm currency before conversion.
3. Do not put an unconditional products→translation foreign key on the supplied
   71-row lookup: 13 products use two untranslated labels. Build a category parent
   from observed nonblank labels with nullable English translation, as proposed
   in the relational model. Missing source categories remain NULL. English labels
   can be exposed through a LEFT JOIN/view; a physical merge is not required.
4. Do not require every order to have items/payments/reviews, impose unique order_id
   in payment/review children, forbid all zero amounts, or enforce flawless event
   chronology. Those constraints would reject retained source records. Keep flags.
5. Do not join raw geolocation directly by prefix. Geographic deduplication and
   representative coordinates need their own review. Retain unmatched prefixes.

Timestamp conflicts, missing delivered stages, unusual shipment deadlines, missing
product metadata, unmatched translations, and payment edge cases should be reviewed
before analytical eligibility rules or duration/retention metrics are implemented.
Their true values cannot be recovered from these files; they should not be 'fixed'
by deleting valid parent records or guessing dates, categories, or amounts. None
of those investigations prevents preservation in staging. No corrections were made.
