-- Shared CTE fragment. The five numbered queries contain an identical copy so
-- they run directly in any SQLite client. The runner checks copies for drift.
-- Each child is independently reduced to one row per order before any joins.
-- Missing child amounts remain NULL; counts of absent children are zero.
WITH RECURSIVE
order_item_summary AS (
    SELECT order_id, COUNT(*) AS item_count,
           SUM(price_hundredths) AS item_sales_hundredths,
           SUM(freight_value_hundredths) AS freight_hundredths,
           SUM(flag_shipping_limit_before_purchase) AS items_shipping_before_purchase,
           SUM(flag_shipping_limit_beyond_purchase_year) AS items_unusual_shipping_year
    FROM order_items GROUP BY order_id
),
payment_summary AS (
    SELECT order_id, SUM(payment_value_hundredths) AS payment_total_hundredths,
           COUNT(*) AS payment_record_count,
           SUM(flag_installments_zero) AS payments_zero_installments,
           SUM(flag_payment_value_zero) AS payments_zero_value,
           SUM(flag_payment_type_undefined) AS payments_undefined_type
    FROM payments GROUP BY order_id
),
review_summary AS (
    SELECT order_id, COUNT(*) AS review_count, SUM(review_score) AS review_score_total,
           -- Exact rational TEXT rather than SQLite AVG's binary float.
           CAST(SUM(review_score) AS TEXT) || '/' || CAST(COUNT(*) AS TEXT) AS average_review_score,
           SUM(flag_title_missing) AS reviews_missing_title,
           SUM(flag_message_missing) AS reviews_missing_message,
           SUM(flag_answer_before_creation) AS reviews_answer_before_creation,
           SUM(flag_creation_before_purchase) AS reviews_creation_before_purchase,
           SUM(flag_creation_on_earlier_purchase_date) AS reviews_earlier_purchase_date,
           SUM(flag_creation_before_purchase_same_date) AS reviews_same_day_before_purchase
    FROM reviews GROUP BY order_id
),
order_level AS (
    SELECT o.*, c.customer_unique_id,
           c.flag_geolocation_missing AS customer_flag_geolocation_missing,
           COALESCE(i.item_count, 0) AS item_count,
           i.item_sales_hundredths, i.freight_hundredths,
           COALESCE(i.items_shipping_before_purchase, 0) AS items_shipping_before_purchase,
           COALESCE(i.items_unusual_shipping_year, 0) AS items_unusual_shipping_year,
           COALESCE(p.payment_record_count, 0) AS payment_record_count,
           p.payment_total_hundredths,
           COALESCE(p.payments_zero_installments, 0) AS payments_zero_installments,
           COALESCE(p.payments_zero_value, 0) AS payments_zero_value,
           COALESCE(p.payments_undefined_type, 0) AS payments_undefined_type,
           COALESCE(r.review_count, 0) AS review_count,
           r.review_score_total, r.average_review_score,
           COALESCE(r.reviews_missing_title, 0) AS reviews_missing_title,
           COALESCE(r.reviews_missing_message, 0) AS reviews_missing_message,
           COALESCE(r.reviews_answer_before_creation, 0) AS reviews_answer_before_creation,
           COALESCE(r.reviews_creation_before_purchase, 0) AS reviews_creation_before_purchase,
           COALESCE(r.reviews_earlier_purchase_date, 0) AS reviews_earlier_purchase_date,
           COALESCE(r.reviews_same_day_before_purchase, 0) AS reviews_same_day_before_purchase
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    LEFT JOIN order_item_summary AS i ON i.order_id = o.order_id
    LEFT JOIN payment_summary AS p ON p.order_id = o.order_id
    LEFT JOIN review_summary AS r ON r.order_id = o.order_id
),
delivered_orders AS (
    SELECT * FROM order_level WHERE order_status = 'delivered'
),
source_bounds AS (
    SELECT MIN(order_purchase_timestamp) AS first_purchase_timestamp,
           MAX(order_purchase_timestamp) AS last_purchase_timestamp,
           MIN(CASE WHEN order_status = 'delivered' THEN SUBSTR(order_purchase_timestamp, 1, 7) END) AS first_completed_purchase_month,
           MAX(CASE WHEN order_status = 'delivered' THEN SUBSTR(order_purchase_timestamp, 1, 7) END) AS last_completed_purchase_month
    FROM orders
)

-- Independent SQL reconciliation of shared aggregates to underlying base tables.
SELECT 'order-level rows' AS check_name,
       (SELECT COUNT(*) FROM orders) AS expected_integer,
       (SELECT COUNT(*) FROM order_level) AS observed_integer
UNION ALL
SELECT 'distinct order-level IDs', (SELECT COUNT(*) FROM orders),
       (SELECT COUNT(DISTINCT order_id) FROM order_level)
UNION ALL
SELECT 'item rows', (SELECT COUNT(*) FROM order_items),
       (SELECT COALESCE(SUM(item_count), 0) FROM order_item_summary)
UNION ALL
SELECT 'item sales hundredths', (SELECT COALESCE(SUM(price_hundredths), 0) FROM order_items),
       (SELECT COALESCE(SUM(item_sales_hundredths), 0) FROM order_item_summary)
UNION ALL
SELECT 'freight hundredths', (SELECT COALESCE(SUM(freight_value_hundredths), 0) FROM order_items),
       (SELECT COALESCE(SUM(freight_hundredths), 0) FROM order_item_summary)
UNION ALL
SELECT 'payment rows', (SELECT COUNT(*) FROM payments),
       (SELECT COALESCE(SUM(payment_record_count), 0) FROM payment_summary)
UNION ALL
SELECT 'payment hundredths', (SELECT COALESCE(SUM(payment_value_hundredths), 0) FROM payments),
       (SELECT COALESCE(SUM(payment_total_hundredths), 0) FROM payment_summary)
UNION ALL
SELECT 'review rows', (SELECT COUNT(*) FROM reviews),
       (SELECT COALESCE(SUM(review_count), 0) FROM review_summary)
UNION ALL
SELECT 'review score sum', (SELECT COALESCE(SUM(review_score), 0) FROM reviews),
       (SELECT COALESCE(SUM(review_score_total), 0) FROM review_summary)
UNION ALL
SELECT 'delivered headers', (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'),
       (SELECT COUNT(*) FROM delivered_orders)
UNION ALL
SELECT 'integer monetary storage violations', 0,
       (SELECT COUNT(*) FROM order_items WHERE TYPEOF(price_hundredths) <> 'integer'
          OR TYPEOF(freight_value_hundredths) <> 'integer')
       + (SELECT COUNT(*) FROM payments WHERE TYPEOF(payment_value_hundredths) <> 'integer');
