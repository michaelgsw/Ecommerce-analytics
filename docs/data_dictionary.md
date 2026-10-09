# Olist Data Dictionary

This dictionary describes all nine CSVs in `data/raw/`. Counts were measured from
the local source files using `src/profile_data.py`; full machine-readable evidence,
including raw-file SHA-256 hashes, is in `data/processed/data_profile.json`.

## Reading this dictionary

- CSV has no native schema. All fields were read as strings to preserve IDs and
  leading zeros. Types below describe the observed content and intended meaning,
  rather than the dtype chosen by an automatic CSV reader.
- `INTEGER` means every present value parsed as a whole number. `DECIMAL` means
  a coordinate or monetary field; this is a logical type, not a proposed SQLite
  storage declaration. `TIMESTAMP` values parsed as `YYYY-MM-DD HH:MM:SS` with no
  timezone information. Every present numeric/date value passed parsing.
- Missing counts include empty fields and whitespace-only fields. Literal text
  such as `NA` is preserved as text. No missing-value replacement was performed.
- Exact duplicate counts are excess occurrences after the first identical parsed
  row, comparing every column and preserving text whitespace. Repeated identifiers
  are separate from duplicate rows.
- Field descriptions use column names and observed contents. Customer identifier
  meanings are confirmed by [Olist's Kaggle documentation](https://www.kaggle.com/olistbr/brazilian-ecommerce/metadata).
  Source money columns have no currency field; confirm currency and semantics
  before reporting monetary KPIs.

## customers

**File:** `olist_customers_dataset.csv`  
**Rows:** 99,441. **Columns:** 5. **Exact duplicate excess rows:** 0.  
**Grain:** One order-associated customer record. **Candidate primary key:**
`customer_id`, with 99,441 distinct values and no missing/repeated keys.

- `customer_id` — TEXT; missing 0. Order-associated customer identifier; join to
  `orders.customer_id`. All values are 32-character lowercase hexadecimal IDs.
- `customer_unique_id` — TEXT; missing 0. Persistent anonymized customer identifier
  across orders; 96,096 distinct values. It is intentionally nonunique here.
- `customer_zip_code_prefix` — TEXT; missing 0. Five-digit delivery postal prefix;
  23,995 rows begin with zero. Preserve the original five characters.
- `customer_city` — TEXT; missing 0. City associated with this order-customer record.
- `customer_state` — TEXT; missing 0. State associated with this record.

No date columns. Do not deduplicate this table on `customer_unique_id`: 2,997
persistent IDs have multiple customer records, and 250 have multiple postal prefixes.
The location belongs to the order-associated record rather than a single permanent
customer address.

## geolocation

**File:** `olist_geolocation_dataset.csv`  
**Rows:** 1,000,163. **Columns:** 5. **Exact duplicate excess rows:** 261,831.  
**Grain:** A postal-prefix coordinate observation. **Source primary key:** None
established; the complete row repeats and the postal prefix is nonunique.

- `geolocation_zip_code_prefix` — TEXT; missing 0. Five-digit postal prefix;
  19,015 distinct values and 245,733 rows beginning with zero. This is a grouping
  and geographic lookup field, not a unique key.
- `geolocation_lat` — DECIMAL; missing 0. Latitude, ranging from
  -36.6053744107061 to 45.06593318269697.
- `geolocation_lng` — DECIMAL; missing 0. Longitude, ranging from
  -101.46676644931476 to 121.10539381057764.
- `geolocation_city` — TEXT; missing 0. Source city label. One value has surrounding
  whitespace. Multiple city labels exist for 8,556 postal prefixes.
- `geolocation_state` — TEXT; missing 0. Source state label. Eight postal prefixes
  have multiple state labels.

No date columns. 390,005 rows belong to exact duplicate groups; retaining one row
per exact group would leave 738,332 observations. These observations still would
not be unique by postal prefix. Coordinates require geographic validation before
choosing a representative coordinate per prefix.

## order_items

**File:** `olist_order_items_dataset.csv`  
**Rows:** 112,650. **Columns:** 7. **Exact duplicate excess rows:** 0.  
**Grain:** One numbered item within an order. **Candidate primary key:**
`(order_id, order_item_id)`, unique and complete across all 112,650 rows.

- `order_id` — TEXT; missing 0. Foreign key to `orders.order_id`.
- `order_item_id` — INTEGER; missing 0. Item sequence within its order, from 1 to 21;
  it is not unique globally and is not an explicit quantity field.
- `product_id` — TEXT; missing 0. Foreign key to `products.product_id`.
- `seller_id` — TEXT; missing 0. Foreign key to `sellers.seller_id`.
- `shipping_limit_date` — TIMESTAMP; missing 0. Source shipment deadline;
  2016-09-19 00:15:34 through 2020-04-09 22:35:08.
- `price` — DECIMAL; missing 0. Source item price, from 0.85 to 6,735.00;
  no zero or negative values.
- `freight_value` — DECIMAL; missing 0. Source item freight amount, from 0.00 to
  409.68; 383 zeros and no negative values.

All three foreign-key columns match their parent tables. Four shipping deadlines
occur after 2018 and require review; the order purchase dates end in 2018.

## order_payments

**File:** `olist_order_payments_dataset.csv`  
**Rows:** 103,886. **Columns:** 5. **Exact duplicate excess rows:** 0.  
**Grain:** One payment record within an order. **Candidate primary key:**
`(order_id, payment_sequential)`, unique and complete across all 103,886 rows.

- `order_id` — TEXT; missing 0. Foreign key to `orders.order_id`; all values match.
- `payment_sequential` — INTEGER; missing 0. Payment sequence within its order,
  from 1 to 29. Multiple records for an order are allowed.
- `payment_type` — TEXT; missing 0. Observed labels: `credit_card`, `boleto`,
  `voucher`, `debit_card`, and `not_defined`.
- `payment_installments` — INTEGER; missing 0. Installment count, from 0 to 24;
  two zero values occur on credit-card records and need review.
- `payment_value` — DECIMAL; missing 0. Payment amount, from 0.00 to 13,664.08;
  nine zeros and no negatives. Zero values include six voucher records and three
  `not_defined` records.

No date columns. One order has no payment record. Payment amount should not be
treated as item sales without reconciling payment and item/freight definitions.

## order_reviews

**File:** `olist_order_reviews_dataset.csv`  
**Rows:** 99,224. **Columns:** 7. **Exact duplicate excess rows:** 0.  
**Grain:** A review associated with an order. **Candidate primary key:**
`(review_id, order_id)`, unique and complete across all 99,224 rows.

- `review_id` — TEXT; missing 0. Source review identifier; 98,410 distinct values.
  It has 814 excess repeated-key rows and cannot be the sole primary key.
- `order_id` — TEXT; missing 0. Foreign key to `orders.order_id`; all values match.
  There are 98,673 distinct order IDs; an order may have multiple reviews.
- `review_score` — INTEGER; missing 0. Score from 1 to 5; no out-of-range values.
- `review_comment_title` — TEXT; missing 87,658: 87,656 empty and two whitespace-only.
  A further 1,996 populated values have surrounding whitespace.
- `review_comment_message` — TEXT; missing 58,274: 58,247 empty and 27 whitespace-only.
  A further 9,424 populated values have surrounding whitespace.
- `review_creation_date` — TIMESTAMP; missing 0. Source review/survey creation date;
  2016-10-02 00:00:00 through 2018-08-31 00:00:00.
- `review_answer_timestamp` — TIMESTAMP; missing 0. Source response timestamp;
  2016-10-07 18:32:28 through 2018-10-29 12:27:35.

789 review IDs relate to multiple orders; 547 orders have multiple review rows.
These are not identical duplicate rows. Do not drop them solely on either ID.
74 review creation timestamps precede the associated order purchase timestamp:
64 are on an earlier calendar date and 10 are on the same day. Most creation values
are midnight; 85 include another time. Same-day cases may reflect source precision
and need interpretation. No response timestamp precedes its creation timestamp.

## orders

**File:** `olist_orders_dataset.csv`  
**Rows:** 99,441. **Columns:** 8. **Exact duplicate excess rows:** 0.  
**Grain:** One order. **Candidate primary key:** `order_id`, unique and complete.
`customer_id` is also unique and complete in this extract, with one matching
customer record per order.

- `order_id` — TEXT; missing 0. Order identifier; parent key for items, payments,
  and reviews.
- `customer_id` — TEXT; missing 0. Foreign key to the order-associated customer
  record; use that record to retrieve `customer_unique_id`.
- `order_status` — TEXT; missing 0. Observed labels: `approved`, `canceled`, `created`,
  `delivered`, `invoiced`, `processing`, `shipped`, and `unavailable`.
- `order_purchase_timestamp` — TIMESTAMP; missing 0.
  Range: 2016-09-04 21:15:19 through 2018-10-17 17:30:18.
- `order_approved_at` — TIMESTAMP; missing 160.
  Range of present values: 2016-09-15 12:16:38 through 2018-09-03 17:40:06.
- `order_delivered_carrier_date` — TIMESTAMP; missing 1,783.
  Range of present values: 2016-10-08 10:34:01 through 2018-09-11 19:48:28.
- `order_delivered_customer_date` — TIMESTAMP; missing 2,965.
  Range of present values: 2016-10-11 13:46:32 through 2018-10-17 13:22:46.
- `order_estimated_delivery_date` — TIMESTAMP; missing 0.
  Range: 2016-09-30 00:00:00 through 2018-11-12 00:00:00.

Absent lifecycle timestamps can reflect order status. Among the 96,478 orders
labeled `delivered`, 14 lack approval time, two lack carrier handoff time, and
eight lack customer delivery time. Preserve these nulls and flag the inconsistencies.

## products

**File:** `olist_products_dataset.csv`  
**Rows:** 32,951. **Columns:** 9. **Exact duplicate excess rows:** 0.  
**Grain:** One product. **Candidate primary key:** `product_id`, unique and complete.

- `product_id` — TEXT; missing 0. Product identifier; parent key for order items.
- `product_category_name` — TEXT; missing 610. Portuguese source category label;
  73 distinct populated categories. Thirteen products use two labels absent from
  the translation table.
- `product_name_lenght` — INTEGER; missing 610. Source product-name length,
  from 5 to 76. The source spelling `lenght` is retained here.
- `product_description_lenght` — INTEGER; missing 610. Source product-description
  length, from 4 to 3,992. The source spelling is retained.
- `product_photos_qty` — INTEGER; missing 610. Source photo count, from 1 to 20.
- `product_weight_g` — INTEGER; missing 2. Weight in grams, from 0 to 40,425;
  four zero weights require review.
- `product_length_cm` — INTEGER; missing 2. Length in centimeters, from 7 to 105.
- `product_height_cm` — INTEGER; missing 2. Height in centimeters, from 2 to 105.
- `product_width_cm` — INTEGER; missing 2. Width in centimeters, from 6 to 118.

No date columns. Missing measurements must remain distinct from zero measurements.

## sellers

**File:** `olist_sellers_dataset.csv`  
**Rows:** 3,095. **Columns:** 4. **Exact duplicate excess rows:** 0.  
**Grain:** One seller. **Candidate primary key:** `seller_id`, unique and complete.

- `seller_id` — TEXT; missing 0. Seller identifier; parent key for order items.
- `seller_zip_code_prefix` — TEXT; missing 0. Five-digit postal prefix;
  1,027 rows begin with zero. Seven prefixes are absent from geolocation.
- `seller_city` — TEXT; missing 0. Source seller city label.
- `seller_state` — TEXT; missing 0. Source seller state label.

No date columns. Seller location is separate from customer delivery location.

## category_translation

**File:** `product_category_name_translation.csv`  
**Rows:** 71. **Columns:** 2. **Exact duplicate excess rows:** 0.  
**Grain:** One supplied category translation. **Candidate primary key:**
`product_category_name`, unique and complete. English names are also unique in
this extract, but should not be the product join key.

- `product_category_name` — TEXT; missing 0. Portuguese category join key.
- `product_category_name_english` — TEXT; missing 0. Supplied English category name.

No date columns. This file has a UTF-8 byte-order mark; use BOM-aware decoding
(`utf-8-sig`) so it does not become part of the first column name.
Source product labels `pc_gamer` and
`portateis_cozinha_e_preparadores_de_alimentos` have no supplied translation.
Preserve these labels and leave their English translation unavailable.

## Relationship and modeling references

See [the profile summary](../reports/data_profile.md) for referential-integrity
counts and cleaning recommendations, and [the proposed SQLite model](sqlite_data_model.md)
for implemented primary keys, foreign keys, storage types, and safe joining rules.

## Prepared-output conventions

The raw field definitions and profiling counts above remain a source snapshot.
The cleaning pipeline adds `source_file`, `source_record_number`, and documented
`flag_` fields to prepared CSVs. Products rename `product_name_lenght` to
`product_name_length` and `product_description_lenght` to
`product_description_length`; the raw names remain unchanged. Structured category
labels are trimmed, lowercased, and whitespace is replaced with underscores.

The pipeline preserves both customer identifiers, uses `(review_id, order_id)` for
review uniqueness, leaves missing attributes unavailable, and stores original-unit
money as exact decimals. Blank CSV fields represent missing values. The implemented
SQLite loader converts them to SQL NULL in prepared tables and preserves exact
parsed text in staging. Money retains decimal TEXT plus exact INTEGER hundredths
of the unspecified source unit; timestamps retain their source format without
an assigned timezone. `data/processed/cleaning_manifest.json` is the generated output
schema and validation record. See [the cleaning report](../reports/cleaning_report.md)
for each flag, measured count, and missing-value decision. Independent database
reconciliation is recorded in [the database report](../reports/database_validation.md).
