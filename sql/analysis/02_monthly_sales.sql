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

-- Purchase-month attribution, with unspecified source timezone.
-- KPIs have the same definitions as sales overview within each calendar month.
-- Customer counts are NOT additive across months. Items sold count item rows.
-- Include every calendar month between ALL-order extract bounds, including gaps.
-- Boundary flags are conservative warnings, not certification of other months.
-- Suppress MoM percentages when either month is an extract/completed-sales
-- boundary or has no orders, or the prior denominator is zero. Changes retain
-- exact integers. Decimal display of rational components happens in Python.
, calendar(month) AS (
    SELECT SUBSTR(first_purchase_timestamp, 1, 7) FROM source_bounds
    WHERE first_purchase_timestamp IS NOT NULL
    UNION ALL
    SELECT STRFTIME('%Y-%m', month || '-01', '+1 month') FROM calendar, source_bounds
    WHERE month < SUBSTR(last_purchase_timestamp, 1, 7)
), monthly AS (
    SELECT cal.month,
           COUNT(o.order_id) AS all_orders,
           COUNT(CASE WHEN o.order_status = 'delivered' THEN 1 END) AS completed_orders,
           COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN o.customer_unique_id END) AS distinct_customers,
           COALESCE(SUM(CASE WHEN o.order_status = 'delivered' THEN o.item_sales_hundredths END), 0) AS item_sales_hundredths,
           COALESCE(SUM(CASE WHEN o.order_status = 'delivered' THEN o.freight_hundredths END), 0) AS freight_hundredths,
           COALESCE(SUM(CASE WHEN o.order_status = 'delivered' THEN o.item_count END), 0) AS items_sold,
           COUNT(CASE WHEN o.order_status = 'delivered' AND o.item_count = 0 THEN 1 END) AS orders_missing_items,
           CAST(cal.month IN (SUBSTR(b.first_purchase_timestamp, 1, 7), SUBSTR(b.last_purchase_timestamp, 1, 7)) AS INTEGER) AS flag_extract_boundary_month,
           CAST(cal.month IN (b.first_completed_purchase_month, b.last_completed_purchase_month) AS INTEGER) AS flag_completed_sales_boundary_month,
           CAST(COUNT(o.order_id) = 0 AS INTEGER) AS flag_no_observed_orders
    FROM calendar AS cal CROSS JOIN source_bounds AS b
    LEFT JOIN order_level AS o ON SUBSTR(o.order_purchase_timestamp, 1, 7) = cal.month
    GROUP BY cal.month
), lagged AS (
    SELECT *, LAG(completed_orders) OVER (ORDER BY month) AS previous_completed_orders,
           LAG(item_sales_hundredths) OVER (ORDER BY month) AS previous_item_sales_hundredths,
           LAG(flag_extract_boundary_month + flag_completed_sales_boundary_month + flag_no_observed_orders)
               OVER (ORDER BY month) AS previous_coverage_warnings
    FROM monthly
), compared AS (
    SELECT *, CAST(previous_completed_orders IS NOT NULL AND previous_coverage_warnings = 0
        AND flag_extract_boundary_month = 0 AND flag_completed_sales_boundary_month = 0
        AND flag_no_observed_orders = 0 AS INTEGER) AS flag_mom_comparable
    FROM lagged
)
SELECT month, all_orders, completed_orders, distinct_customers,
       item_sales_hundredths, freight_hundredths, items_sold, orders_missing_items,
       item_sales_hundredths AS average_order_value_hundredths_numerator,
       completed_orders AS average_order_value_hundredths_denominator,
       flag_extract_boundary_month, flag_completed_sales_boundary_month,
       flag_no_observed_orders, flag_mom_comparable,
       previous_completed_orders, previous_item_sales_hundredths,
       completed_orders - previous_completed_orders AS completed_orders_mom_change,
       item_sales_hundredths - previous_item_sales_hundredths AS item_sales_mom_change_hundredths,
       CASE WHEN flag_mom_comparable = 1 AND previous_completed_orders > 0
            THEN 100 * (completed_orders - previous_completed_orders) END AS completed_orders_mom_percent_numerator,
       CASE WHEN flag_mom_comparable = 1 AND previous_completed_orders > 0
            THEN previous_completed_orders END AS completed_orders_mom_percent_denominator,
       CASE WHEN flag_mom_comparable = 1 AND previous_item_sales_hundredths > 0
            THEN 100 * (item_sales_hundredths - previous_item_sales_hundredths) END AS item_sales_mom_percent_numerator,
       CASE WHEN flag_mom_comparable = 1 AND previous_item_sales_hundredths > 0
            THEN previous_item_sales_hundredths END AS item_sales_mom_percent_denominator
FROM compared ORDER BY month;
