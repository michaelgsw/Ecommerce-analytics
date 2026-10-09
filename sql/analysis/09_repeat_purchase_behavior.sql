-- result: repeat_purchase_summary
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


, first_repeat AS (SELECT * FROM repeat_intervals WHERE purchase_number=2),
ranked_first_repeat AS (SELECT *, ROW_NUMBER() OVER (ORDER BY repeat_interval_days, customer_unique_id) AS interval_rank, COUNT(*) OVER () AS repeat_customers FROM first_repeat)
-- Conditional on 2+ observed delivered orders. Not a probability among all first-time customers.
SELECT 'repeat_customers' AS metric, COUNT(*) AS count, NULL AS value_numerator, NULL AS value_denominator FROM first_repeat
UNION ALL SELECT 'median_days_to_second_purchase', MAX(repeat_customers), SUM(repeat_interval_days), COUNT(*) FROM ranked_first_repeat WHERE interval_rank IN ((repeat_customers+1)/2,(repeat_customers+2)/2)
UNION ALL SELECT 'same_day_second_purchase', SUM(repeat_interval_days=0), 100*SUM(repeat_interval_days=0), COUNT(*) FROM first_repeat
UNION ALL SELECT 'first_second_timestamp_ties', COALESCE(SUM(flag_tied_purchase_timestamp),0), NULL, NULL FROM first_repeat
UNION ALL SELECT 'all_consecutive_repeat_intervals', COUNT(*), NULL, NULL FROM repeat_intervals
UNION ALL SELECT 'within_30_days', SUM(repeat_interval_days<=30), 100*SUM(repeat_interval_days<=30), COUNT(*) FROM first_repeat
UNION ALL SELECT 'within_60_days', SUM(repeat_interval_days<=60), 100*SUM(repeat_interval_days<=60), COUNT(*) FROM first_repeat
UNION ALL SELECT 'within_90_days', SUM(repeat_interval_days<=90), 100*SUM(repeat_interval_days<=90), COUNT(*) FROM first_repeat
UNION ALL SELECT 'within_180_days', SUM(repeat_interval_days<=180), 100*SUM(repeat_interval_days<=180), COUNT(*) FROM first_repeat;

-- result: repeat_interval_distribution
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

-- Calendar-day bins, separately for first-to-second and every consecutive repeat interval.
, all_intervals AS (SELECT 'first_to_second' AS scope, repeat_interval_days FROM repeat_intervals WHERE purchase_number=2
 UNION ALL SELECT 'all_consecutive', repeat_interval_days FROM repeat_intervals), bins AS (
 SELECT *, CASE WHEN repeat_interval_days=0 THEN '01_same_day' WHEN repeat_interval_days<=30 THEN '02_1_to_30_days'
 WHEN repeat_interval_days<=60 THEN '03_31_to_60_days' WHEN repeat_interval_days<=90 THEN '04_61_to_90_days'
 WHEN repeat_interval_days<=180 THEN '05_91_to_180_days' WHEN repeat_interval_days<=365 THEN '06_181_to_365_days'
 ELSE '07_over_365_days' END AS interval_bin FROM all_intervals)
SELECT scope, interval_bin, COUNT(*) AS intervals, MIN(repeat_interval_days) AS min_days, MAX(repeat_interval_days) AS max_days
FROM bins GROUP BY scope, interval_bin ORDER BY scope, interval_bin;

-- result: category_transitions
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

-- First aggregate item facts to order/category, then profiles to one row per order.
-- Compare ALL consecutive completed orders; first-to-second is also separately reported.
-- Any missing category/empty order makes comparison unknown, never same-category NULL.
, order_categories AS (SELECT i.order_id, p.product_category_name, COUNT(*) AS items
 FROM order_items AS i JOIN products AS p USING(product_id) GROUP BY i.order_id,p.product_category_name),
profiles AS (SELECT order_id, COUNT(product_category_name) AS known_categories, SUM(product_category_name IS NULL) AS missing_categories FROM order_categories GROUP BY order_id),
pair_profiles AS (SELECT r.*, old.known_categories AS old_known, new.known_categories AS new_known,
 COALESCE(old.missing_categories,1)+COALESCE(new.missing_categories,1) AS missing_categories,
 (SELECT COUNT(*) FROM order_categories AS a JOIN order_categories AS b ON a.product_category_name=b.product_category_name
  WHERE a.order_id=r.previous_order_id AND b.order_id=r.order_id AND a.product_category_name IS NOT NULL) AS matching_categories
 FROM repeat_intervals AS r LEFT JOIN profiles AS old ON old.order_id=r.previous_order_id LEFT JOIN profiles AS new ON new.order_id=r.order_id),
classified_pairs AS (SELECT *, CASE WHEN missing_categories>0 OR old_known=0 OR new_known=0 THEN 'category_unknown'
 WHEN matching_categories=old_known AND matching_categories=new_known THEN 'same_category_set'
 WHEN matching_categories>0 THEN 'overlap_with_change' ELSE 'no_category_overlap' END AS behavior FROM pair_profiles),
scoped AS (SELECT 'all_consecutive' AS scope,* FROM classified_pairs UNION ALL SELECT 'first_to_second',* FROM classified_pairs WHERE purchase_number=2)
SELECT scope, behavior, COUNT(*) AS order_transitions, COUNT(DISTINCT customer_unique_id) AS distinct_customers,
 SUM(flag_tied_purchase_timestamp) AS tied_timestamp_transitions,
 100*COUNT(*) AS transition_share_percent_numerator,
 (SELECT COUNT(*) FROM scoped AS total WHERE total.scope=s.scope) AS transition_share_percent_denominator
FROM scoped AS s GROUP BY scope,behavior ORDER BY scope,behavior;

-- result: category_customer_behavior
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

-- Each order/category is aggregated BEFORE joining persistent customer classifications.
-- Sales/item totals are additive within frequency group; category customer/order counts overlap.
, order_categories AS (SELECT i.order_id,p.product_category_name,COUNT(*) AS items_purchased,SUM(i.price_hundredths) AS item_sales_hundredths
 FROM order_items AS i JOIN products AS p USING(product_id) GROUP BY i.order_id,p.product_category_name),
category_sales AS (SELECT s.frequency_group, oc.product_category_name,pc.product_category_name_english,
 COUNT(DISTINCT s.customer_unique_id) AS customers,COUNT(DISTINCT o.order_id) AS completed_orders,
 SUM(oc.items_purchased) AS items_purchased,SUM(oc.item_sales_hundredths) AS item_sales_hundredths
 FROM order_categories AS oc JOIN completed_purchases AS o USING(order_id)
 JOIN customer_classified AS s USING(customer_unique_id)
 LEFT JOIN product_categories AS pc ON pc.product_category_name=oc.product_category_name
 GROUP BY s.frequency_group,oc.product_category_name,pc.product_category_name_english),
ranked AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY frequency_group ORDER BY item_sales_hundredths DESC,product_category_name) AS sales_rank,
 SUM(item_sales_hundredths) OVER(PARTITION BY frequency_group) AS group_sales_hundredths FROM category_sales)
SELECT frequency_group,product_category_name,product_category_name_english,customers,completed_orders,items_purchased,item_sales_hundredths,sales_rank,
 100*item_sales_hundredths AS group_sales_share_percent_numerator,group_sales_hundredths AS group_sales_share_percent_denominator
FROM ranked ORDER BY frequency_group,sales_rank;
