# Olist Data Profile

This is the original profiling snapshot, before implementation of cleaning.
The subsequent [cleaning report](cleaning_report.md) records the implemented rules
and measured outcomes; findings below remain unchanged as source evidence.

**Scope:** Structural profiling and data-quality review of all nine local CSVs.
No sales, product-performance, geographic-performance, or retention analysis was
performed. No cleaning logic, SQLite database, or transformed dataset was created.

## Evidence and method

Run `python src/profile_data.py` from the project root after installing the project
requirements. If its generated JSON already exists, use
`python src/profile_data.py --overwrite` to intentionally regenerate that JSON.
The script never writes to `data/raw/`.

This run used Python 3.12.14 and pandas 3.0.1 from the bundled runtime. The complete
results are in `data/processed/data_profile.json`. All nine CSV SHA-256 hashes were
checked before and after profiling and remained unchanged. Counts include every
parsed CSV record, excluding headers, and correctly handle quoted multiline text.
An independent standard-library CSV check confirmed all row counts, missing counts,
duplicate counts, and date ranges. Each CSV's bytes also matched its original entry
in the downloaded ZIP archive.

Missing values include empty and whitespace-only fields. Duplicate counts below
are excess identical rows after the first occurrence, comparing all original
parsed field values. No trimming, deduplication, or imputation was applied. Types
are content-based logical types, with IDs and postal prefixes preserved as text.
All tested present timestamps, numeric values, 32-character hexadecimal IDs, and
five-digit postal prefixes passed their parsing/format checks.

All 52 columns, their types, missing counts, and applicable date ranges are in
[the data dictionary](../docs/data_dictionary.md).

## File inventory and keys

- **customers:** 99,441 rows, 5 columns, 0 exact duplicate excess rows.
  `customer_id` is unique and complete. `customer_unique_id` has 96,096 distinct
  values and is intentionally nonunique in this table.
- **geolocation:** 1,000,163 rows, 5 columns, 261,831 exact duplicate excess rows.
  No source primary key was established. Its 19,015 postal prefixes are nonunique.
- **order_items:** 112,650 rows, 7 columns, 0 exact duplicate excess rows.
  `(order_id, order_item_id)` is unique and complete.
- **order_payments:** 103,886 rows, 5 columns, 0 exact duplicate excess rows.
  `(order_id, payment_sequential)` is unique and complete.
- **order_reviews:** 99,224 rows, 7 columns, 0 exact duplicate excess rows.
  `(review_id, order_id)` is unique and complete; neither individual ID is unique.
- **orders:** 99,441 rows, 8 columns, 0 exact duplicate excess rows.
  Both `order_id` and `customer_id` are unique and complete in this extract.
- **products:** 32,951 rows, 9 columns, 0 exact duplicate excess rows.
  `product_id` is unique and complete.
- **sellers:** 3,095 rows, 4 columns, 0 exact duplicate excess rows.
  `seller_id` is unique and complete.
- **category_translation:** 71 rows, 2 columns, 0 exact duplicate excess rows.
  `product_category_name` is unique and complete.

## Relationships verified against the files

- `customers.customer_id` to `orders.customer_id`: exactly one-to-one in this
  extract. All 99,441 records match on both sides.
- `orders.order_id` to `order_items.order_id`: one-to-zero-or-many; no orphan item
  rows. There are 775 orders without items: 603 `unavailable`, 164 `canceled`, five
  `created`, two `invoiced`, and one `shipped`.
- `products.product_id` and `sellers.seller_id` to their order-item columns:
  one-to-many. No orphan product or seller references were found; every product
  and seller in these files is referenced by at least one item.
- `orders.order_id` to `order_payments.order_id`: one-to-zero-or-many; no orphan
  payment rows. One order lacks a payment record. The maximum is 29 payment records
  for a single order.
- `orders.order_id` to `order_reviews.order_id`: one-to-zero-or-many; no orphan
  review rows. 768 orders lack a review, while 547 orders have multiple review rows.
  The maximum is three review rows per order.
- `category_translation.product_category_name` to `products.product_category_name`:
  one-to-many for supplied translations. 610 products have no category; 13 products
  use two nonblank categories with no translation: `pc_gamer` and
  `portateis_cozinha_e_preparadores_de_alimentos`.
- Postal-prefix matching to geolocation is a coverage lookup, not a foreign key
  to a unique parent. 278 customer records across 157 prefixes and seven seller
  records across seven prefixes have no matching geolocation observation.

Use left joins when preserving orders/products with missing optional children or
translations. Joining item, payment, and review detail directly creates row
multiplication. Aggregate each child to the intended grain separately before
combining future analytical outputs. Do not join raw geolocation directly to orders
or customers by prefix; multiple observations will multiply rows.

## Customer identity

Olist documents `customer_id` as an identifier assigned separately to each order,
and `customer_unique_id` as the identifier for linking the same anonymized customer
across purchases. [Source: Olist's customer documentation](https://www.kaggle.com/olistbr/brazilian-ecommerce/metadata).

The files contain 99,441 order-associated customer IDs and 96,096 persistent IDs.
2,997 persistent IDs map to multiple customer IDs, with a maximum of 17 customer
records for one persistent ID. These are identity/grain checks, not a calculated
repeat-purchase KPI. Later customer-level counts and cohorts must use
`customer_unique_id` after joining orders through `customer_id` and defining order
eligibility. 250 persistent IDs have multiple postal prefixes, so preserve locations
at the order-customer level.

## Main data-quality issues and their implications

1. **Geolocation is redundant and ambiguous.** 261,831 exact duplicate excess rows
   exist, and 8,556 prefixes have multiple city labels. Eight prefixes have multiple
   state labels. All coordinates fit global latitude/longitude limits, but 29 rows
   fall outside a deliberately broad Brazil screening rectangle: latitude -35 to 6
   and longitude -75 to -30. This heuristic flags candidates for review, not verified
   border violations or a deletion rule. A simple average or first-row lookup could
   produce misleading locations.
2. **Review IDs are reused.** `review_id` has 814 excess repeated-key rows; 789 review
   IDs appear under multiple orders. None of those reused IDs has conflicting scores,
   but their order associations must be preserved. The pair `(review_id, order_id)`
   is unique. A sole `review_id` primary key or deduplication by `order_id` would lose
   source records.
3. **Missing text and product attributes need explicit null handling.** Review titles
   have 87,658 missing values and messages have 58,274, including two and 27
   whitespace-only fields respectively. Missing comments do not invalidate scores.
   Product category, name length, description length, and photo count each have 610
   missing values. Weight and each dimension have two missing values; four products
   have zero weight. Untranslated categories must not cause product rows to disappear.
4. **Lifecycle timestamps are incomplete or inconsistent.** Approval time is missing
   in 160 orders, carrier time in 1,783, and customer delivery time in 2,965. Many
   blanks correspond to non-delivered statuses. Among orders labeled `delivered`,
   14 lack approval time, two lack carrier time, and eight lack delivery time. On rows
   where both relevant timestamps exist, 166 carrier times precede purchase, 1,359
   precede approval, and 23 delivery times precede carrier handoff. These sets can
   overlap and must not be summed as unique affected orders. No approval or customer
   delivery time precedes purchase in the comparable records.
5. **Some dates require source review.** Purchases run from 2016-09-04 21:15:19 to
   2018-10-17 17:30:18. Four item shipping deadlines fall after 2018, with the maximum
   in 2020. 74 review creation times precede their associated order purchase: 64 are
   on an earlier calendar date and 10 are on the same day. Most creation values are
   midnight; same-day cases may reflect timestamp precision. The causes are
   unconfirmed; do not repair years or timestamps by assumption. Different
   event date ranges are not evidence of complete monthly coverage.
6. **Payment edge cases need interpretation.** Two credit-card payment records have
   zero installments. Nine payment records have zero value: six vouchers and three
   `not_defined` records. One order has no payment. Preserve and flag these records;
   do not assume a missing payment equals zero sales. Item prices are positive;
   freight has 383 zero values, which can be legitimate.
7. **Text representation and postal codes matter.** One geolocation city label and
   many populated review comments have surrounding whitespace. Leading-zero postal
   prefixes occur in 23,995 customer records, 245,733 geolocation records, and 1,027
   seller records. Numeric import would lose their original representation. The
   translation CSV has a UTF-8 byte-order mark; BOM-aware decoding prevents an
   invisible character from being retained in its first column name.

## Recommended cleaning steps, not yet implemented

1. Preserve raw CSVs and load a lossless staging layer with file/record lineage.
2. Convert empty/whitespace-only fields to SQL `NULL` in prepared tables. Preserve
   review text originals; add normalized text only where a defined use requires it.
3. Decode CSVs using `utf-8-sig` to handle the translation file's byte-order mark.
   Keep IDs and five-digit postal prefixes as text. Parse nullable whole-number
   measurements and timestamps explicitly, without assigning an unverified timezone.
   Use decimal parsing for money and select exact storage after confirming currency.
4. Preserve every order-associated customer record. Add a distinct persistent
   customer entity keyed by `customer_unique_id`; keep delivery location on the
   source customer record.
5. Keep the validated composite item, payment, and review keys. Flag source key
   violations on future loads rather than silently dropping records.
6. Build categories from observed labels and left-join supplied translations.
   Retain untranslated Portuguese labels and missing English values; do not invent
   translations or turn unknown categories into observed categories.
7. Retain all geolocation observations in staging. Review coordinate outliers and
   conflicting city/state labels before deduplicating a prepared geographic layer.
   Choose and document a deterministic representative-coordinate method after that
   review. Provide one lookup row per observed prefix, including prefixes lacking
   coordinates, and preserve unmatched customer/seller records.
8. Add timestamp, product-measurement, and payment quality flags. Keep nullable
   lifecycle dates; do not fill them with purchase or estimated delivery dates.
   Apply metric-specific exclusions later only after defining their business rules.
9. Reconcile row counts, keys, nulls, and foreign-key coverage after each future
   transformation. Validate each join's intended grain before calculating KPIs.

## Recommended next task

Agree on the documented null, geography, anomaly, and monetary-storage policies,
then implement a beginner-readable SQLite ingestion pipeline with staging tables,
the [proposed relational model](../docs/sqlite_data_model.md), quality flags, and
source-to-database reconciliation. Keep business analysis deferred until ingestion
and validation are complete. The source lacks explicit discount, refund, tax, cost,
and currency fields; planned net-sales, return, and margin KPIs need a feasibility
review before implementation.
