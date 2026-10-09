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

-- ALL statuses; no completed-sales eligibility filter.
-- Status share = 100 * status orders / all orders. Cancellation, unavailable,
-- and delivered rates use the corresponding status numerator over ALL orders.
-- Missing children = actual zero child-record counts, not NULL source IDs.
-- Every order flag and aggregated item/payment/review flag remains visible.
-- Flags can overlap; their sums are not distinct affected-order counts.
, operational_totals AS (
    SELECT COUNT(*) AS all_orders,
           COALESCE(SUM(order_status = 'canceled'), 0) AS canceled_orders,
           COALESCE(SUM(order_status = 'unavailable'), 0) AS unavailable_orders,
           COALESCE(SUM(order_status = 'delivered'), 0) AS delivered_orders
    FROM order_level
)
SELECT o.order_status, COUNT(*) AS orders,
       100 * COUNT(*) AS status_share_percent_numerator,
       t.all_orders AS status_share_percent_denominator,
       100 * t.canceled_orders AS cancellation_rate_percent_numerator,
       t.all_orders AS cancellation_rate_percent_denominator,
       100 * t.unavailable_orders AS unavailable_order_rate_percent_numerator,
       t.all_orders AS unavailable_order_rate_percent_denominator,
       100 * t.delivered_orders AS delivered_order_rate_percent_numerator,
       t.all_orders AS delivered_order_rate_percent_denominator,
       SUM(item_count = 0) AS orders_missing_items,
       SUM(payment_record_count = 0) AS orders_missing_payments,
       SUM(review_count = 0) AS orders_missing_reviews,
       SUM(flag_approval_before_purchase) AS flag_approval_before_purchase,
       SUM(flag_carrier_before_purchase) AS flag_carrier_before_purchase,
       SUM(flag_carrier_before_approval) AS flag_carrier_before_approval,
       SUM(flag_delivery_before_purchase) AS flag_delivery_before_purchase,
       SUM(flag_delivery_before_carrier) AS flag_delivery_before_carrier,
       SUM(flag_delivered_missing_order_approved_at) AS flag_delivered_missing_order_approved_at,
       SUM(flag_delivered_missing_order_delivered_carrier_date) AS flag_delivered_missing_order_delivered_carrier_date,
       SUM(flag_delivered_missing_order_delivered_customer_date) AS flag_delivered_missing_order_delivered_customer_date,
       SUM(flag_items_missing) AS flag_items_missing,
       SUM(flag_payments_missing) AS flag_payments_missing,
       SUM(flag_reviews_missing) AS flag_reviews_missing,
       SUM(customer_flag_geolocation_missing) AS customer_flag_geolocation_missing,
       SUM(items_shipping_before_purchase) AS items_shipping_before_purchase,
       SUM(items_unusual_shipping_year) AS items_unusual_shipping_year,
       SUM(payments_zero_installments) AS payments_zero_installments,
       SUM(payments_zero_value) AS payments_zero_value,
       SUM(payments_undefined_type) AS payments_undefined_type,
       SUM(reviews_missing_title) AS reviews_missing_title,
       SUM(reviews_missing_message) AS reviews_missing_message,
       SUM(reviews_answer_before_creation) AS reviews_answer_before_creation,
       SUM(reviews_creation_before_purchase) AS reviews_creation_before_purchase,
       SUM(reviews_earlier_purchase_date) AS reviews_earlier_purchase_date,
       SUM(reviews_same_day_before_purchase) AS reviews_same_day_before_purchase
FROM order_level AS o CROSS JOIN operational_totals AS t
GROUP BY o.order_status ORDER BY orders DESC, o.order_status;
