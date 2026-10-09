# SQLite Database Validation

Validation run (UTC): 2026-10-05T21:45:14+00:00. User reporting timezone: America/New_York.

**PASS: 118 checks; 0 failures.** Database: `data/database/olist_analytics.db`.
SQLite runtime: 3.53.1. Database SHA-256: `b5d332fc0edde0d40800a5f5fa65b8f7ebafea7091e65e3bef907d1d6ba5eac7`.

## Independent method

The standard-library validator opens SQLite read-only and rereads the eight processed CSVs. It imports neither cleaning functions nor loader/conversion functions. Each prepared value is matched by its validated primary key, including exact text, INTEGER types, quality flags, lineage, NULL positions, decimal amounts, and timestamp format. Each staging CSV record is compared field by field as original parsed text, including blank fields and multiline prose. CSV counts are recomputed, not taken from the cleaning manifest. The saved SQL checks are also executed.

## Row reconciliation

- `customers`: processed CSV 99,441; database 99,441; staging 99,441; difference 0.
- `orders`: processed CSV 99,441; database 99,441; staging 99,441; difference 0.
- `products`: processed CSV 32,951; database 32,951; staging 32,951; difference 0.
- `sellers`: processed CSV 3,095; database 3,095; staging 3,095; difference 0.
- `order_items`: processed CSV 112,650; database 112,650; staging 112,650; difference 0.
- `payments`: processed CSV 103,886; database 103,886; staging 103,886; difference 0.
- `reviews`: processed CSV 99,224; database 99,224; staging 99,224; difference 0.
- `product_categories`: distinct nonblank product/translation label union 73; database 73; difference 0.
- `stg_category_translation`: processed CSV 71; database 71; difference 0.

The seven entity staging tables retain exactly the same row counts as their corresponding prepared tables. The 71 supplied translations are retained in `stg_category_translation`; the category parent contains 73 observed labels and two NULL English translations.

## Storage, NULLs, numbers, and timestamps

IDs, postal prefixes, and populated prose remain exact TEXT. Missing optional values become SQL NULL only in prepared tables; staging keeps the exact blank text. Every flag becomes INTEGER 0/1, and lineage is retained. No source data or quality flags are dropped.

`price`, `freight_value`, and `payment_value` retain their exact CSV decimal strings as TEXT. Their companion `price_hundredths`, `freight_value_hundredths`, and `payment_value_hundredths` columns store exact INTEGER hundredths of the unspecified source unit. Every amount was checked with Decimal, including scale, nonnegativity, finite values, equality per row, and exact aggregate reconciliation. No binary float or rounding is used. The builder rejects future amounts that cannot fit this scale or the signed 64-bit INTEGER range. These columns do not assert a currency or define sales eligibility. Use the integer companions for exact SQL arithmetic; SUM/CAST of the text amounts can invoke SQLite floating-point arithmetic. Keep totals in hundredths and format with Decimal outside SQLite; `/100.0` is approximate display.

All eight timestamp columns are parsed strictly as `YYYY-MM-DD HH:MM:SS`, stored as TEXT, and checked per row and by count/minimum/maximum. No timezone is assigned. No timestamp chronology constraint is imposed.

### Missing values preserved (CSV / SQL)

- `orders.order_delivered_carrier_date`: 1,783 / 1,783.
- `orders.order_delivered_customer_date`: 2,965 / 2,965.
- `orders.order_approved_at`: 160 / 160.
- `products.product_category_name`: 610 / 610.
- `products.product_name_length`: 610 / 610.
- `products.product_description_length`: 610 / 610.
- `products.product_photos_qty`: 610 / 610.
- `products.product_weight_g`: 2 / 2.
- `products.product_length_cm`: 2 / 2.
- `products.product_height_cm`: 2 / 2.
- `products.product_width_cm`: 2 / 2.
- `reviews.review_comment_title`: 87,658 / 87,658.
- `reviews.review_comment_message`: 58,274 / 58,274.
- `product_categories.product_category_name_english`: 2 / 2.

All other prepared fields have zero missing values on both sides. Every NULL position, rather than just its count, was checked. Category English NULLs are derived from absent supplied translations.

### Timestamp coverage

- `orders.order_purchase_timestamp`: 99,441 populated; `2016-09-04 21:15:19` through `2018-10-17 17:30:18`; exact match.
- `orders.order_approved_at`: 99,281 populated; `2016-09-15 12:16:38` through `2018-09-03 17:40:06`; exact match.
- `orders.order_delivered_carrier_date`: 97,658 populated; `2016-10-08 10:34:01` through `2018-09-11 19:48:28`; exact match.
- `orders.order_delivered_customer_date`: 96,476 populated; `2016-10-11 13:46:32` through `2018-10-17 13:22:46`; exact match.
- `orders.order_estimated_delivery_date`: 99,441 populated; `2016-09-30 00:00:00` through `2018-11-12 00:00:00`; exact match.
- `order_items.shipping_limit_date`: 112,650 populated; `2016-09-19 00:15:34` through `2020-04-09 22:35:08`; exact match.
- `reviews.review_creation_date`: 99,224 populated; `2016-10-02 00:00:00` through `2018-08-31 00:00:00`; exact match.
- `reviews.review_answer_timestamp`: 99,224 populated; `2016-10-07 18:32:28` through `2018-10-29 12:27:35`; exact match.

## Keys, foreign keys, and indexes

All eight prepared primary keys are explicitly NOT NULL, declared as specified, and independently checked for duplicate groups. No duplicate groups or foreign-key violations were found; SQLite integrity_check returned `ok`.

- `customers` primary key: `(customer_id)`.
- `orders` primary key: `(order_id)`.
- `products` primary key: `(product_id)`.
- `sellers` primary key: `(seller_id)`.
- `order_items` primary key: `(order_id, order_item_id)`.
- `payments` primary key: `(order_id, payment_sequential)`.
- `reviews` primary key: `(review_id, order_id)`.
- `product_categories` primary key: `(product_category_name)`.

All seven foreign keys use ON UPDATE NO ACTION / ON DELETE NO ACTION:

- `order_items.order_id` → `orders.order_id`.
- `order_items.product_id` → `products.product_id`.
- `order_items.seller_id` → `sellers.seller_id`.
- `orders.customer_id` → `customers.customer_id`.
- `payments.order_id` → `orders.order_id`.
- `products.product_category_name` → `product_categories.product_category_name`.
- `reviews.order_id` → `orders.order_id`.

Every index (including SQLite's automatic primary-key indexes):

- `idx_customers_customer_unique_id` on `customers(customer_unique_id)`: nonunique analytical join.
- `sqlite_autoindex_customers_1` on `customers(customer_id)`: unique primary-key.
- `idx_orders_customer_id` on `orders(customer_id)`: nonunique analytical join.
- `sqlite_autoindex_orders_1` on `orders(order_id)`: unique primary-key.
- `idx_products_category` on `products(product_category_name)`: nonunique analytical join.
- `sqlite_autoindex_products_1` on `products(product_id)`: unique primary-key.
- `sqlite_autoindex_sellers_1` on `sellers(seller_id)`: unique primary-key.
- `idx_order_items_seller_id` on `order_items(seller_id)`: nonunique analytical join.
- `idx_order_items_product_id` on `order_items(product_id)`: nonunique analytical join.
- `sqlite_autoindex_order_items_1` on `order_items(order_id, order_item_id)`: unique primary-key.
- `sqlite_autoindex_payments_1` on `payments(order_id, payment_sequential)`: unique primary-key.
- `idx_reviews_order_id` on `reviews(order_id)`: nonunique analytical join.
- `sqlite_autoindex_reviews_1` on `reviews(review_id, order_id)`: unique primary-key.
- `sqlite_autoindex_product_categories_1` on `product_categories(product_category_name)`: unique primary-key.

The composite PK indexes cover `order_items.order_id` and `payments.order_id` through their leading columns; redundant single-column indexes are omitted. Staging tables have no explicit indexes or uniqueness constraints. ANALYZE supplies planner statistics.

## Complete constraints

All project tables are STRICT (SQLite 3.37 or newer). Prepared required operational fields, lineage, and flags are NOT NULL; optional product metadata, lifecycle timestamps, review text, and category English names remain nullable. Staging columns are TEXT NOT NULL, accepting blank strings. Checks permit Boolean flags 0/1; review scores 1–5; positive item/payment sequences and lineage record numbers; nonnegative product metadata, installments, and integer monetary companions; the eight observed order statuses; the five observed payment types; and a nonblank category key. The exact prepared DDL below exhaustively records every NOT NULL, CHECK, PK, and FK constraint.

```sql
CREATE TABLE customers (
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix TEXT NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    source_file TEXT NOT NULL,
    flag_geolocation_missing INTEGER NOT NULL CHECK (flag_geolocation_missing IN (0, 1)),
    PRIMARY KEY (customer_id)
) STRICT;
```

```sql
CREATE TABLE orders (
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL CHECK (order_status IN ('approved', 'canceled', 'created', 'delivered', 'invoiced', 'processing', 'shipped', 'unavailable')),
    order_purchase_timestamp TEXT NOT NULL,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    flag_approval_before_purchase INTEGER NOT NULL CHECK (flag_approval_before_purchase IN (0, 1)),
    flag_carrier_before_purchase INTEGER NOT NULL CHECK (flag_carrier_before_purchase IN (0, 1)),
    flag_carrier_before_approval INTEGER NOT NULL CHECK (flag_carrier_before_approval IN (0, 1)),
    flag_delivery_before_purchase INTEGER NOT NULL CHECK (flag_delivery_before_purchase IN (0, 1)),
    flag_delivery_before_carrier INTEGER NOT NULL CHECK (flag_delivery_before_carrier IN (0, 1)),
    flag_delivered_missing_order_approved_at INTEGER NOT NULL CHECK (flag_delivered_missing_order_approved_at IN (0, 1)),
    flag_delivered_missing_order_delivered_carrier_date INTEGER NOT NULL CHECK (flag_delivered_missing_order_delivered_carrier_date IN (0, 1)),
    flag_delivered_missing_order_delivered_customer_date INTEGER NOT NULL CHECK (flag_delivered_missing_order_delivered_customer_date IN (0, 1)),
    source_file TEXT NOT NULL,
    flag_items_missing INTEGER NOT NULL CHECK (flag_items_missing IN (0, 1)),
    flag_payments_missing INTEGER NOT NULL CHECK (flag_payments_missing IN (0, 1)),
    flag_reviews_missing INTEGER NOT NULL CHECK (flag_reviews_missing IN (0, 1)),
    PRIMARY KEY (order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE NO ACTION ON DELETE NO ACTION
) STRICT;
```

```sql
CREATE TABLE products (
    product_id TEXT NOT NULL,
    product_category_name TEXT,
    product_name_length INTEGER CHECK (product_name_length >= 0),
    product_description_length INTEGER CHECK (product_description_length >= 0),
    product_photos_qty INTEGER CHECK (product_photos_qty >= 0),
    product_weight_g INTEGER CHECK (product_weight_g >= 0),
    product_length_cm INTEGER CHECK (product_length_cm >= 0),
    product_height_cm INTEGER CHECK (product_height_cm >= 0),
    product_width_cm INTEGER CHECK (product_width_cm >= 0),
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    flag_category_missing INTEGER NOT NULL CHECK (flag_category_missing IN (0, 1)),
    flag_weight_zero INTEGER NOT NULL CHECK (flag_weight_zero IN (0, 1)),
    source_file TEXT NOT NULL,
    flag_category_translation_missing INTEGER NOT NULL CHECK (flag_category_translation_missing IN (0, 1)),
    PRIMARY KEY (product_id),
    FOREIGN KEY (product_category_name) REFERENCES product_categories(product_category_name) ON UPDATE NO ACTION ON DELETE NO ACTION
) STRICT;
```

```sql
CREATE TABLE sellers (
    seller_id TEXT NOT NULL,
    seller_zip_code_prefix TEXT NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    source_file TEXT NOT NULL,
    flag_geolocation_missing INTEGER NOT NULL CHECK (flag_geolocation_missing IN (0, 1)),
    PRIMARY KEY (seller_id)
) STRICT;
```

```sql
CREATE TABLE order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL CHECK (order_item_id > 0),
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TEXT NOT NULL,
    price TEXT NOT NULL,
    freight_value TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    source_file TEXT NOT NULL,
    flag_shipping_limit_before_purchase INTEGER NOT NULL CHECK (flag_shipping_limit_before_purchase IN (0, 1)),
    flag_shipping_limit_beyond_purchase_year INTEGER NOT NULL CHECK (flag_shipping_limit_beyond_purchase_year IN (0, 1)),
    price_hundredths INTEGER NOT NULL CHECK (price_hundredths >= 0),
    freight_value_hundredths INTEGER NOT NULL CHECK (freight_value_hundredths >= 0),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON UPDATE NO ACTION ON DELETE NO ACTION,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE NO ACTION ON DELETE NO ACTION,
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON UPDATE NO ACTION ON DELETE NO ACTION
) STRICT;
```

```sql
CREATE TABLE payments (
    order_id TEXT NOT NULL,
    payment_sequential INTEGER NOT NULL CHECK (payment_sequential > 0),
    payment_type TEXT NOT NULL CHECK (payment_type IN ('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined')),
    payment_installments INTEGER NOT NULL CHECK (payment_installments >= 0),
    payment_value TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    flag_installments_zero INTEGER NOT NULL CHECK (flag_installments_zero IN (0, 1)),
    flag_payment_value_zero INTEGER NOT NULL CHECK (flag_payment_value_zero IN (0, 1)),
    flag_payment_type_undefined INTEGER NOT NULL CHECK (flag_payment_type_undefined IN (0, 1)),
    source_file TEXT NOT NULL,
    payment_value_hundredths INTEGER NOT NULL CHECK (payment_value_hundredths >= 0),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON UPDATE NO ACTION ON DELETE NO ACTION
) STRICT;
```

```sql
CREATE TABLE reviews (
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT NOT NULL,
    review_answer_timestamp TEXT NOT NULL,
    source_record_number INTEGER NOT NULL CHECK (source_record_number > 0),
    flag_title_missing INTEGER NOT NULL CHECK (flag_title_missing IN (0, 1)),
    flag_message_missing INTEGER NOT NULL CHECK (flag_message_missing IN (0, 1)),
    flag_answer_before_creation INTEGER NOT NULL CHECK (flag_answer_before_creation IN (0, 1)),
    source_file TEXT NOT NULL,
    flag_creation_before_purchase INTEGER NOT NULL CHECK (flag_creation_before_purchase IN (0, 1)),
    flag_creation_on_earlier_purchase_date INTEGER NOT NULL CHECK (flag_creation_on_earlier_purchase_date IN (0, 1)),
    flag_creation_before_purchase_same_date INTEGER NOT NULL CHECK (flag_creation_before_purchase_same_date IN (0, 1)),
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON UPDATE NO ACTION ON DELETE NO ACTION
) STRICT;
```

```sql
CREATE TABLE product_categories (
    product_category_name TEXT NOT NULL PRIMARY KEY CHECK (TRIM(product_category_name) <> ''),
    product_category_name_english TEXT
) STRICT;
```

No UNIQUE constraint exists on customer_unique_id, orders.customer_id, payments.order_id, reviews.order_id, or review_id alone. There are no chronology checks, parent-must-have-child requirements, positive-only money/weight/installment requirements, or postal/geolocation foreign keys.

## Retained source edge cases and issues

- orders.order_approved_at: NULL count: 160 retained records/groups.
- orders.order_delivered_carrier_date: NULL count: 1,783 retained records/groups.
- orders.order_delivered_customer_date: NULL count: 2,965 retained records/groups.
- products.product_category_name: NULL count: 610 retained records/groups.
- products.product_name_length: NULL count: 610 retained records/groups.
- products.product_description_length: NULL count: 610 retained records/groups.
- products.product_photos_qty: NULL count: 610 retained records/groups.
- products.product_weight_g: NULL count: 2 retained records/groups.
- products.product_length_cm: NULL count: 2 retained records/groups.
- products.product_height_cm: NULL count: 2 retained records/groups.
- products.product_width_cm: NULL count: 2 retained records/groups.
- reviews.review_comment_title: NULL count: 87,658 retained records/groups.
- reviews.review_comment_message: NULL count: 58,274 retained records/groups.
- product_categories.product_category_name_english: NULL count: 2 retained records/groups.
- canceled orders: 625 retained records/groups.
- unavailable orders: 609 retained records/groups.
- orders without items: 775 retained records/groups.
- orders without payments: 1 retained records/groups.
- orders without reviews: 768 retained records/groups.
- zero freight values: 383 retained records/groups.
- zero payment values: 9 retained records/groups.
- zero installments: 2 retained records/groups.
- undefined payment methods: 3 retained records/groups.
- zero product weights: 4 retained records/groups.
- repeated persistent customer ID groups: 2,997 retained records/groups.
- repeated review ID groups: 789 retained records/groups.
- orders with multiple payments: 2,961 retained records/groups.
- orders with multiple reviews: 547 retained records/groups.
- carrier handoff before purchase: 166 retained records/groups.
- carrier handoff before approval: 1,359 retained records/groups.
- customer delivery before carrier: 23 retained records/groups.
- review creation before purchase: 74 retained records/groups.
- unusual shipment years (flag retained): 4 retained records/groups.
- delivered orders missing approval: 14 retained records/groups.
- delivered orders missing carrier handoff: 2 retained records/groups.
- delivered orders missing delivery: 8 retained records/groups.

These are existing source conditions, not loading defects. Missing categories/metadata, untranslated labels, zero payment/installment/weight values, missing delivered stages, unusual shipment deadlines, and timestamp conflicts still require metric-specific interpretation. Flags preserve the evidence. Repeated customer/review identifiers and split payments remain intact. See the independent source validation report for context; no repair was guessed.

## Preservation and rebuild

All 23 files under data/raw/ and data/processed/ had identical before/after SHA-256 hashes. Processed CSV hashes also matched the completed cleaning manifest. No geolocation table was loaded or joined; only its file bytes were hashed for preservation.

```powershell
.\.venv\Scripts\python.exe -m src.database.build_database
```

A rebuild creates and validates a temporary database beside the destination, checks protected input hashes, and then atomically replaces only the database file. A failed prepublication check leaves the previous database intact. Close SQL clients before rebuilding on Windows. Database and Markdown/JSON report publication are separate filesystem operations. Run one builder/validator at a time and verify the database hash in the evidence after interruption.

Recheck without rebuilding:

```powershell
.\.venv\Scripts\python.exe -m src.database.validate_database
```

## SQL analysis readiness

**The database is structurally safe to use for SQL business analysis.** All loading and reconciliation checks pass; no confirmed database defects remain. Metric eligibility and currency semantics still need agreement, and anomaly flags need appropriate treatment for duration or retention metrics. Preserve parents with LEFT JOIN where needed; aggregate items, payments, and reviews separately to the intended grain before joining them to avoid multiplication. Use customer_unique_id for customer-level analytics after joining through customer_id. Enable PRAGMA foreign_keys = ON on every future writing connection. No business KPIs or geolocation analyses have been started.
