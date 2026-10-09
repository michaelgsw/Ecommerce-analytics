-- result: frequency_distribution
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

-- Counts represent distinct persistent customers, not order-associated customer records.
SELECT completed_order_count, COUNT(*) AS customers, SUM(item_sales_hundredths) AS item_sales_hundredths,
       SUM(freight_hundredths) AS freight_hundredths,
       100 * COUNT(*) AS customer_share_percent_numerator,
       (SELECT COUNT(*) FROM customer_level) AS customer_share_percent_denominator
FROM customer_level GROUP BY completed_order_count ORDER BY completed_order_count;

-- result: value_distribution
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

-- Empirical quartile bins; ties are never split by label.
, binned AS (SELECT c.*, CASE WHEN item_sales_hundredths <= t.q1_hundredths THEN '01_at_or_below_Q1'
 WHEN item_sales_hundredths <= t.median_hundredths THEN '02_Q1_to_median'
 WHEN item_sales_hundredths <= t.q3_hundredths THEN '03_median_to_Q3'
 ELSE '04_above_Q3' END AS value_bin FROM customer_level AS c CROSS JOIN customer_thresholds AS t)
SELECT value_bin, COUNT(*) AS customers, MIN(item_sales_hundredths) AS min_sales_hundredths,
 MAX(item_sales_hundredths) AS max_sales_hundredths, SUM(item_sales_hundredths) AS item_sales_hundredths
FROM binned GROUP BY value_bin ORDER BY value_bin;

-- result: value_statistics
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

-- Nearest-rank empirical quantiles; no interpolated binary floating-point percentiles.
SELECT 'minimum' AS statistic, 'hundredths' AS unit, MIN(item_sales_hundredths) AS value_numerator, 1 AS value_denominator FROM customer_level
UNION ALL SELECT 'Q1', 'hundredths', q1_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'median', 'hundredths', median_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'Q3', 'hundredths', q3_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'P90', 'hundredths', p90_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'P95', 'hundredths', p95_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'P99', 'hundredths', p99_hundredths, 1 FROM customer_thresholds
UNION ALL SELECT 'maximum', 'hundredths', MAX(item_sales_hundredths), 1 FROM customer_level
UNION ALL SELECT 'mean', 'hundredths', SUM(item_sales_hundredths), COUNT(*) FROM customer_level
UNION ALL SELECT 'Tukey_upper_fence', 'hundredths', 2*q3_hundredths+3*(q3_hundredths-q1_hundredths), 2 FROM customer_thresholds
UNION ALL SELECT 'recency_median', 'calendar_days', recency_median_days, 1 FROM customer_thresholds;

-- result: purchase_group_comparison
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

-- A customer group is assigned once from its complete observed delivered-order history.
SELECT frequency_group, COUNT(*) AS customers, SUM(completed_order_count) AS completed_orders,
 SUM(item_sales_hundredths) AS item_sales_hundredths, SUM(freight_hundredths) AS freight_hundredths,
 SUM(item_sales_hundredths) AS average_customer_sales_hundredths_numerator, COUNT(*) AS average_customer_sales_hundredths_denominator,
 SUM(item_sales_hundredths) AS average_order_value_hundredths_numerator, SUM(completed_order_count) AS average_order_value_hundredths_denominator,
 100*SUM(item_sales_hundredths) AS sales_share_percent_numerator,
 (SELECT SUM(item_sales_hundredths) FROM customer_level) AS sales_share_percent_denominator
FROM customer_classified GROUP BY frequency_group ORDER BY frequency_group;

-- result: pareto_concentration
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

-- Exact top ceil(N*p/100) customers. ID resolves cutoff ties deterministically;
-- identical-value ties can straddle a Pareto cutoff, but segment thresholds do not split ties.
, pareto_ranked AS (SELECT customer_unique_id, item_sales_hundredths,
 ROW_NUMBER() OVER (ORDER BY item_sales_hundredths DESC, customer_unique_id) AS value_rank,
 COUNT(*) OVER () AS total_customers,
 SUM(item_sales_hundredths) OVER () AS total_sales_hundredths,
 SUM(item_sales_hundredths) OVER (ORDER BY item_sales_hundredths DESC, customer_unique_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_sales_hundredths
 FROM customer_level), percent_grid(p) AS (SELECT 1 UNION ALL SELECT p+1 FROM percent_grid WHERE p<100)
SELECT g.p AS target_customer_percent, r.value_rank AS customers_selected, r.total_customers,
 100*r.value_rank AS actual_customer_percent_numerator, r.total_customers AS actual_customer_percent_denominator,
 r.cumulative_sales_hundredths AS item_sales_hundredths,
 100*r.cumulative_sales_hundredths AS cumulative_sales_percent_numerator, r.total_sales_hundredths AS cumulative_sales_percent_denominator,
 r.item_sales_hundredths AS cutoff_customer_sales_hundredths
FROM percent_grid AS g JOIN pareto_ranked AS r ON r.value_rank=(r.total_customers*g.p+99)/100 ORDER BY g.p;

-- result: customers_for_80_percent_sales
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

-- Calculate concentration, never assume an 80/20 rule.
, p AS (SELECT ROW_NUMBER() OVER (ORDER BY item_sales_hundredths DESC, customer_unique_id) AS value_rank,
 COUNT(*) OVER () AS total_customers, SUM(item_sales_hundredths) OVER () AS total_sales_hundredths,
 SUM(item_sales_hundredths) OVER (ORDER BY item_sales_hundredths DESC, customer_unique_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_sales_hundredths
 FROM customer_level)
SELECT 80 AS target_sales_percent, value_rank AS customers_selected, cumulative_sales_hundredths AS item_sales_hundredths,
 100*value_rank AS customer_share_percent_numerator, total_customers AS customer_share_percent_denominator,
 100*cumulative_sales_hundredths AS sales_share_percent_numerator, total_sales_hundredths AS sales_share_percent_denominator
FROM p WHERE 100*cumulative_sales_hundredths >= 80*total_sales_hundredths ORDER BY value_rank LIMIT 1;

-- result: recency_summary
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

-- Relative to latest observed completed purchase date, never to today's date.
-- Neutral halves use the empirical nearest-rank median and retain all median ties.
SELECT recency_group, observation_date, recency_median_days, COUNT(*) AS customers,
 MIN(recency_days) AS min_recency_days, MAX(recency_days) AS max_recency_days,
 SUM(item_sales_hundredths) AS item_sales_hundredths,
 SUM(flag_customer_state_unassigned) AS customers_state_unassigned
FROM customer_classified GROUP BY recency_group, observation_date, recency_median_days ORDER BY recency_group;
