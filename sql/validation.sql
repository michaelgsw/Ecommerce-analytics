-- Read-only database checks. The Python validator additionally compares every field
-- against the processed CSVs with independent Decimal/datetime parsers.
PRAGMA integrity_check;

PRAGMA foreign_key_check;

SELECT 'customers' AS table_name, COUNT(*) AS records FROM customers
UNION ALL
SELECT 'orders' AS table_name, COUNT(*) AS records FROM orders
UNION ALL
SELECT 'products' AS table_name, COUNT(*) AS records FROM products
UNION ALL
SELECT 'sellers' AS table_name, COUNT(*) AS records FROM sellers
UNION ALL
SELECT 'order_items' AS table_name, COUNT(*) AS records FROM order_items
UNION ALL
SELECT 'payments' AS table_name, COUNT(*) AS records FROM payments
UNION ALL
SELECT 'reviews' AS table_name, COUNT(*) AS records FROM reviews
UNION ALL
SELECT 'product_categories' AS table_name, COUNT(*) AS records FROM product_categories
UNION ALL
SELECT 'stg_customers' AS table_name, COUNT(*) AS records FROM stg_customers
UNION ALL
SELECT 'stg_orders' AS table_name, COUNT(*) AS records FROM stg_orders
UNION ALL
SELECT 'stg_products' AS table_name, COUNT(*) AS records FROM stg_products
UNION ALL
SELECT 'stg_sellers' AS table_name, COUNT(*) AS records FROM stg_sellers
UNION ALL
SELECT 'stg_order_items' AS table_name, COUNT(*) AS records FROM stg_order_items
UNION ALL
SELECT 'stg_payments' AS table_name, COUNT(*) AS records FROM stg_payments
UNION ALL
SELECT 'stg_reviews' AS table_name, COUNT(*) AS records FROM stg_reviews
UNION ALL
SELECT 'stg_category_translation' AS table_name, COUNT(*) AS records FROM stg_category_translation;

SELECT 'customers: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM customers GROUP BY customer_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'orders: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM orders GROUP BY order_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'products: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM products GROUP BY product_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'sellers: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM sellers GROUP BY seller_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'order_items: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM order_items GROUP BY order_id, order_item_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'payments: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM payments GROUP BY order_id, payment_sequential HAVING COUNT(*) > 1)
UNION ALL
SELECT 'reviews: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM reviews GROUP BY review_id, order_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'product_categories: duplicate primary key groups' AS check_name, COUNT(*) AS violations FROM (SELECT 1 FROM product_categories GROUP BY product_category_name HAVING COUNT(*) > 1);

SELECT 'orders.customer_id: orphan references' AS check_name, COUNT(*) AS violations FROM orders AS child LEFT JOIN customers AS parent ON child.customer_id = parent.customer_id WHERE child.customer_id IS NOT NULL AND parent.customer_id IS NULL
UNION ALL
SELECT 'products.product_category_name: orphan references' AS check_name, COUNT(*) AS violations FROM products AS child LEFT JOIN product_categories AS parent ON child.product_category_name = parent.product_category_name WHERE child.product_category_name IS NOT NULL AND parent.product_category_name IS NULL
UNION ALL
SELECT 'order_items.order_id: orphan references' AS check_name, COUNT(*) AS violations FROM order_items AS child LEFT JOIN orders AS parent ON child.order_id = parent.order_id WHERE child.order_id IS NOT NULL AND parent.order_id IS NULL
UNION ALL
SELECT 'order_items.product_id: orphan references' AS check_name, COUNT(*) AS violations FROM order_items AS child LEFT JOIN products AS parent ON child.product_id = parent.product_id WHERE child.product_id IS NOT NULL AND parent.product_id IS NULL
UNION ALL
SELECT 'order_items.seller_id: orphan references' AS check_name, COUNT(*) AS violations FROM order_items AS child LEFT JOIN sellers AS parent ON child.seller_id = parent.seller_id WHERE child.seller_id IS NOT NULL AND parent.seller_id IS NULL
UNION ALL
SELECT 'payments.order_id: orphan references' AS check_name, COUNT(*) AS violations FROM payments AS child LEFT JOIN orders AS parent ON child.order_id = parent.order_id WHERE child.order_id IS NOT NULL AND parent.order_id IS NULL
UNION ALL
SELECT 'reviews.order_id: orphan references' AS check_name, COUNT(*) AS violations FROM reviews AS child LEFT JOIN orders AS parent ON child.order_id = parent.order_id WHERE child.order_id IS NOT NULL AND parent.order_id IS NULL;

SELECT 'order_items: monetary storage types/domains' AS check_name, COUNT(*) AS violations
FROM order_items WHERE typeof(price) <> 'text' OR typeof(freight_value) <> 'text'
OR typeof(price_hundredths) <> 'integer' OR typeof(freight_value_hundredths) <> 'integer'
OR price_hundredths < 0 OR freight_value_hundredths < 0
UNION ALL
SELECT 'payments: monetary storage types/domains', COUNT(*) FROM payments
WHERE typeof(payment_value) <> 'text' OR typeof(payment_value_hundredths) <> 'integer'
OR payment_value_hundredths < 0;

SELECT 'orders.order_approved_at: NULL count' AS observation, COUNT(*) AS records FROM orders WHERE order_approved_at IS NULL
UNION ALL
SELECT 'orders.order_delivered_carrier_date: NULL count' AS observation, COUNT(*) AS records FROM orders WHERE order_delivered_carrier_date IS NULL
UNION ALL
SELECT 'orders.order_delivered_customer_date: NULL count' AS observation, COUNT(*) AS records FROM orders WHERE order_delivered_customer_date IS NULL
UNION ALL
SELECT 'products.product_category_name: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_category_name IS NULL
UNION ALL
SELECT 'products.product_name_length: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_name_length IS NULL
UNION ALL
SELECT 'products.product_description_length: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_description_length IS NULL
UNION ALL
SELECT 'products.product_photos_qty: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_photos_qty IS NULL
UNION ALL
SELECT 'products.product_weight_g: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_weight_g IS NULL
UNION ALL
SELECT 'products.product_length_cm: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_length_cm IS NULL
UNION ALL
SELECT 'products.product_height_cm: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_height_cm IS NULL
UNION ALL
SELECT 'products.product_width_cm: NULL count' AS observation, COUNT(*) AS records FROM products WHERE product_width_cm IS NULL
UNION ALL
SELECT 'reviews.review_comment_title: NULL count' AS observation, COUNT(*) AS records FROM reviews WHERE review_comment_title IS NULL
UNION ALL
SELECT 'reviews.review_comment_message: NULL count' AS observation, COUNT(*) AS records FROM reviews WHERE review_comment_message IS NULL
UNION ALL
SELECT 'product_categories.product_category_name_english: NULL count' AS observation, COUNT(*) AS records FROM product_categories WHERE product_category_name_english IS NULL;

-- Observations below are retained coverage/anomalies, NOT constraint failures.
SELECT 'canceled orders' AS observation, (SELECT COUNT(*) FROM orders WHERE order_status = 'canceled') AS records
UNION ALL
SELECT 'unavailable orders' AS observation, (SELECT COUNT(*) FROM orders WHERE order_status = 'unavailable') AS records
UNION ALL
SELECT 'orders without items' AS observation, (SELECT COUNT(*) FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM order_items AS i WHERE i.order_id = o.order_id)) AS records
UNION ALL
SELECT 'orders without payments' AS observation, (SELECT COUNT(*) FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM payments AS p WHERE p.order_id = o.order_id)) AS records
UNION ALL
SELECT 'orders without reviews' AS observation, (SELECT COUNT(*) FROM orders AS o WHERE NOT EXISTS (SELECT 1 FROM reviews AS r WHERE r.order_id = o.order_id)) AS records
UNION ALL
SELECT 'zero freight values' AS observation, (SELECT COUNT(*) FROM order_items WHERE freight_value_hundredths = 0) AS records
UNION ALL
SELECT 'zero payment values' AS observation, (SELECT COUNT(*) FROM payments WHERE payment_value_hundredths = 0) AS records
UNION ALL
SELECT 'zero installments' AS observation, (SELECT COUNT(*) FROM payments WHERE payment_installments = 0) AS records
UNION ALL
SELECT 'undefined payment methods' AS observation, (SELECT COUNT(*) FROM payments WHERE payment_type = 'not_defined') AS records
UNION ALL
SELECT 'zero product weights' AS observation, (SELECT COUNT(*) FROM products WHERE product_weight_g = 0) AS records
UNION ALL
SELECT 'repeated persistent customer ID groups' AS observation, (SELECT COUNT(*) FROM (SELECT customer_unique_id FROM customers GROUP BY customer_unique_id HAVING COUNT(*) > 1)) AS records
UNION ALL
SELECT 'repeated review ID groups' AS observation, (SELECT COUNT(*) FROM (SELECT review_id FROM reviews GROUP BY review_id HAVING COUNT(*) > 1)) AS records
UNION ALL
SELECT 'orders with multiple payments' AS observation, (SELECT COUNT(*) FROM (SELECT order_id FROM payments GROUP BY order_id HAVING COUNT(*) > 1)) AS records
UNION ALL
SELECT 'orders with multiple reviews' AS observation, (SELECT COUNT(*) FROM (SELECT order_id FROM reviews GROUP BY order_id HAVING COUNT(*) > 1)) AS records
UNION ALL
SELECT 'carrier handoff before purchase' AS observation, (SELECT COUNT(*) FROM orders WHERE order_delivered_carrier_date < order_purchase_timestamp) AS records
UNION ALL
SELECT 'carrier handoff before approval' AS observation, (SELECT COUNT(*) FROM orders WHERE order_delivered_carrier_date < order_approved_at) AS records
UNION ALL
SELECT 'customer delivery before carrier' AS observation, (SELECT COUNT(*) FROM orders WHERE order_delivered_customer_date < order_delivered_carrier_date) AS records
UNION ALL
SELECT 'review creation before purchase' AS observation, (SELECT COUNT(*) FROM reviews AS r JOIN orders AS o USING(order_id) WHERE r.review_creation_date < o.order_purchase_timestamp) AS records
UNION ALL
SELECT 'unusual shipment years (flag retained)' AS observation, (SELECT COUNT(*) FROM order_items WHERE flag_shipping_limit_beyond_purchase_year = 1) AS records
UNION ALL
SELECT 'delivered orders missing approval' AS observation, (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_approved_at IS NULL) AS records
UNION ALL
SELECT 'delivered orders missing carrier handoff' AS observation, (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_carrier_date IS NULL) AS records
UNION ALL
SELECT 'delivered orders missing delivery' AS observation, (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL) AS records;

SELECT name AS index_name, tbl_name AS table_name, sql AS definition FROM sqlite_schema WHERE type='index' ORDER BY tbl_name, name;
