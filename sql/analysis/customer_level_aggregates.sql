-- Read-only customer-grain CTE fragment; no persistent table/view or row-level export.
-- Delivered purchases only. customer_id is a bridge to persistent customer_unique_id.
-- Money stays INTEGER hundredths. Date differences use integer calendar-day counters,
-- not elapsed durations or an inferred timezone for source event timestamps.
WITH RECURSIVE
customer_item_by_order AS (
    SELECT order_id, COUNT(*) AS items_purchased,
           SUM(price_hundredths) AS item_sales_hundredths,
           SUM(freight_value_hundredths) AS freight_hundredths
    FROM order_items GROUP BY order_id
), completed_purchases AS (
    SELECT o.order_id, c.customer_unique_id, c.customer_state,
           o.order_purchase_timestamp, DATE(o.order_purchase_timestamp) AS purchase_date,
           SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_month,
           i.item_sales_hundredths, i.freight_hundredths,
           COALESCE(i.items_purchased, 0) AS items_purchased
    FROM orders AS o JOIN customers AS c ON c.customer_id = o.customer_id
    LEFT JOIN customer_item_by_order AS i ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered'
), customer_base AS (
    SELECT customer_unique_id, MIN(purchase_date) AS first_purchase_date,
           MAX(purchase_date) AS last_purchase_date, COUNT(*) AS completed_order_count,
           COALESCE(SUM(item_sales_hundredths), 0) AS item_sales_hundredths,
           COALESCE(SUM(freight_hundredths), 0) AS freight_hundredths,
           SUM(items_purchased) AS items_purchased,
           SUM(items_purchased = 0) AS orders_missing_items,
           COUNT(DISTINCT NULLIF(TRIM(customer_state), '')) AS distinct_customer_states,
           SUM(customer_state IS NULL OR TRIM(customer_state) = '') AS orders_missing_state,
           CASE WHEN COUNT(DISTINCT NULLIF(TRIM(customer_state), '')) = 1
                     AND SUM(customer_state IS NULL OR TRIM(customer_state) = '') = 0
                THEN MIN(customer_state) END AS customer_state
    FROM completed_purchases GROUP BY customer_unique_id
), customer_observation AS (
    SELECT MAX(purchase_date) AS observation_date,
           MIN(purchase_month) AS first_completed_month,
           MAX(purchase_month) AS last_completed_month
    FROM completed_purchases
), customer_level AS (
    SELECT b.*, b.item_sales_hundredths AS average_order_value_hundredths_numerator,
           b.completed_order_count AS average_order_value_hundredths_denominator,
           CAST(b.item_sales_hundredths AS TEXT) || '/' || CAST(b.completed_order_count AS TEXT) AS average_order_value_hundredths,
           (CAST(STRFTIME('%s', b.last_purchase_date) AS INTEGER)
               - CAST(STRFTIME('%s', b.first_purchase_date) AS INTEGER)) / 86400 AS days_between_first_and_last_purchase,
           CAST(b.completed_order_count >= 2 AS INTEGER) AS repeat_customer_flag,
           o.observation_date,
           (CAST(STRFTIME('%s', o.observation_date) AS INTEGER)
               - CAST(STRFTIME('%s', b.last_purchase_date) AS INTEGER)) / 86400 AS recency_days,
           SUBSTR(b.first_purchase_date, 1, 7) AS cohort_month,
           CAST(b.customer_state IS NULL AS INTEGER) AS flag_customer_state_unassigned
    FROM customer_base AS b CROSS JOIN customer_observation AS o
), customer_ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY item_sales_hundredths, customer_unique_id) AS value_rank_ascending,
           ROW_NUMBER() OVER (ORDER BY recency_days, customer_unique_id) AS recency_rank_ascending,
           COUNT(*) OVER () AS total_customers
    FROM customer_level
), customer_thresholds AS (
    SELECT MAX(total_customers) AS total_customers,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 25 + 99) / 100 THEN item_sales_hundredths END) AS q1_hundredths,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 50 + 99) / 100 THEN item_sales_hundredths END) AS median_hundredths,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 75 + 99) / 100 THEN item_sales_hundredths END) AS q3_hundredths,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 90 + 99) / 100 THEN item_sales_hundredths END) AS p90_hundredths,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 95 + 99) / 100 THEN item_sales_hundredths END) AS p95_hundredths,
           MAX(CASE WHEN value_rank_ascending = (total_customers * 99 + 99) / 100 THEN item_sales_hundredths END) AS p99_hundredths,
           MAX(CASE WHEN recency_rank_ascending = (total_customers * 50 + 99) / 100 THEN recency_days END) AS recency_median_days
    FROM customer_ranked
), customer_classified AS (
    SELECT c.*,
           CASE WHEN repeat_customer_flag = 1 THEN 'Repeat' ELSE 'One-time' END AS frequency_group,
           CAST(2 * c.item_sales_hundredths > 2 * t.q3_hundredths + 3 * (t.q3_hundredths - t.q1_hundredths) AS INTEGER) AS high_value_flag,
           CASE WHEN recency_days <= t.recency_median_days THEN 'recent within observed period'
                ELSE 'less recent within observed period' END AS recency_group,
           t.q1_hundredths, t.q3_hundredths, t.recency_median_days,
           2 * t.q3_hundredths + 3 * (t.q3_hundredths - t.q1_hundredths) AS high_value_threshold_hundredths_numerator,
           2 AS high_value_threshold_hundredths_denominator
    FROM customer_level AS c CROSS JOIN customer_thresholds AS t
), customer_segments AS (
    SELECT *, CASE
        WHEN high_value_flag = 1 AND repeat_customer_flag = 1 THEN 'High-value repeat'
        WHEN high_value_flag = 0 AND repeat_customer_flag = 1 THEN 'Standard repeat'
        WHEN high_value_flag = 1 THEN 'High-value one-time'
        ELSE 'Standard one-time' END AS segment
    FROM customer_classified
), ranked_purchases AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp, order_id) AS purchase_number,
           LAG(order_id) OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp, order_id) AS previous_order_id,
           LAG(purchase_date) OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp, order_id) AS previous_purchase_date,
           LAG(order_purchase_timestamp) OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp, order_id) AS previous_purchase_timestamp
    FROM completed_purchases
), repeat_intervals AS (
    SELECT *, (CAST(STRFTIME('%s', purchase_date) AS INTEGER)
             - CAST(STRFTIME('%s', previous_purchase_date) AS INTEGER)) / 86400 AS repeat_interval_days,
           CAST(order_purchase_timestamp = previous_purchase_timestamp AS INTEGER) AS flag_tied_purchase_timestamp
    FROM ranked_purchases WHERE purchase_number >= 2
)
