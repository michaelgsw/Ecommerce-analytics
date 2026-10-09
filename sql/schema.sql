-- Prepared CSV staging: exact parsed text, including blank fields.
-- STRICT requires SQLite >= 3.37. Enable foreign_keys on EVERY writing connection.
-- Timestamp parsing and exact monetary reconciliation also run in Python.
PRAGMA foreign_keys = ON;

CREATE TABLE stg_customers (
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix TEXT NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_geolocation_missing TEXT NOT NULL
) STRICT;

CREATE TABLE stg_orders (
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TEXT NOT NULL,
    order_approved_at TEXT NOT NULL,
    order_delivered_carrier_date TEXT NOT NULL,
    order_delivered_customer_date TEXT NOT NULL,
    order_estimated_delivery_date TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    flag_approval_before_purchase TEXT NOT NULL,
    flag_carrier_before_purchase TEXT NOT NULL,
    flag_carrier_before_approval TEXT NOT NULL,
    flag_delivery_before_purchase TEXT NOT NULL,
    flag_delivery_before_carrier TEXT NOT NULL,
    flag_delivered_missing_order_approved_at TEXT NOT NULL,
    flag_delivered_missing_order_delivered_carrier_date TEXT NOT NULL,
    flag_delivered_missing_order_delivered_customer_date TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_items_missing TEXT NOT NULL,
    flag_payments_missing TEXT NOT NULL,
    flag_reviews_missing TEXT NOT NULL
) STRICT;

CREATE TABLE stg_order_items (
    order_id TEXT NOT NULL,
    order_item_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TEXT NOT NULL,
    price TEXT NOT NULL,
    freight_value TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_shipping_limit_before_purchase TEXT NOT NULL,
    flag_shipping_limit_beyond_purchase_year TEXT NOT NULL
) STRICT;

CREATE TABLE stg_products (
    product_id TEXT NOT NULL,
    product_category_name TEXT NOT NULL,
    product_name_length TEXT NOT NULL,
    product_description_length TEXT NOT NULL,
    product_photos_qty TEXT NOT NULL,
    product_weight_g TEXT NOT NULL,
    product_length_cm TEXT NOT NULL,
    product_height_cm TEXT NOT NULL,
    product_width_cm TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    flag_category_missing TEXT NOT NULL,
    flag_weight_zero TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_category_translation_missing TEXT NOT NULL
) STRICT;

CREATE TABLE stg_payments (
    order_id TEXT NOT NULL,
    payment_sequential TEXT NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments TEXT NOT NULL,
    payment_value TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    flag_installments_zero TEXT NOT NULL,
    flag_payment_value_zero TEXT NOT NULL,
    flag_payment_type_undefined TEXT NOT NULL,
    source_file TEXT NOT NULL
) STRICT;

CREATE TABLE stg_reviews (
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_score TEXT NOT NULL,
    review_comment_title TEXT NOT NULL,
    review_comment_message TEXT NOT NULL,
    review_creation_date TEXT NOT NULL,
    review_answer_timestamp TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    flag_title_missing TEXT NOT NULL,
    flag_message_missing TEXT NOT NULL,
    flag_answer_before_creation TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_creation_before_purchase TEXT NOT NULL,
    flag_creation_on_earlier_purchase_date TEXT NOT NULL,
    flag_creation_before_purchase_same_date TEXT NOT NULL
) STRICT;

CREATE TABLE stg_sellers (
    seller_id TEXT NOT NULL,
    seller_zip_code_prefix TEXT NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    source_file TEXT NOT NULL,
    flag_geolocation_missing TEXT NOT NULL
) STRICT;

CREATE TABLE stg_category_translation (
    product_category_name TEXT NOT NULL,
    product_category_name_english TEXT NOT NULL,
    source_record_number TEXT NOT NULL,
    source_file TEXT NOT NULL
) STRICT;

-- Observed labels from products and the supplied translation lookup; no inventions.
CREATE TABLE product_categories (
    product_category_name TEXT NOT NULL PRIMARY KEY CHECK (TRIM(product_category_name) <> ''),
    product_category_name_english TEXT
) STRICT;

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

-- Leading columns of the composite PK indexes already cover order_items.order_id
-- and payments.order_id. Repeating those single-column indexes adds no join benefit.
CREATE INDEX idx_customers_customer_unique_id ON customers(customer_unique_id);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_seller_id ON order_items(seller_id);
CREATE INDEX idx_reviews_order_id ON reviews(order_id);
CREATE INDEX idx_products_category ON products(product_category_name);
-- No parent-must-have-children, timestamp chronology, or standalone review-ID uniqueness rules.
