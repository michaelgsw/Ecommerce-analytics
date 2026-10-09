-- result: customer_cohort_summary
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
-- Append to customer_level_aggregates.sql. Each customer enters one first-observed
-- completed-purchase cohort. Activity is deduplicated to customer/month BEFORE joins.
-- A cohort's original size is every retention denominator; month 0 is membership,
-- not repeat retention. Future/gap/terminal-partial rates are NULL, not zeros.
, cohort_customers AS (
    SELECT cohort_month, COUNT(*) AS new_customers,
           SUM(completed_order_count) AS completed_orders,
           SUM(repeat_customer_flag) AS repeat_customers,
           SUM(item_sales_hundredths) AS item_sales_hundredths,
           SUM(freight_hundredths) AS freight_hundredths,
           SUM(items_purchased) AS items_purchased
    FROM customer_level GROUP BY cohort_month
), customer_month_activity AS (
    SELECT c.cohort_month, p.customer_unique_id, p.purchase_month, COUNT(*) AS orders_in_month
    FROM completed_purchases AS p JOIN customer_level AS c USING(customer_unique_id)
    GROUP BY c.cohort_month, p.customer_unique_id, p.purchase_month
), cohort_activity AS (
    SELECT cohort_month, purchase_month, COUNT(*) AS observed_customers,
           SUM(orders_in_month >= 2 AND cohort_month = purchase_month) AS same_month_repeat_customers
    FROM customer_month_activity GROUP BY cohort_month, purchase_month
), all_order_month_counts AS (
    SELECT SUBSTR(order_purchase_timestamp, 1, 7) AS month, COUNT(*) AS all_orders
    FROM orders GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
), cohort_horizon(month_index) AS (
    SELECT 0 UNION ALL SELECT month_index + 1 FROM cohort_horizon, customer_observation
    WHERE month_index < MAX(3,
        12 * (CAST(SUBSTR(last_completed_month, 1, 4) AS INTEGER) - CAST(SUBSTR(first_completed_month, 1, 4) AS INTEGER))
        + CAST(SUBSTR(last_completed_month, 6, 2) AS INTEGER) - CAST(SUBSTR(first_completed_month, 6, 2) AS INTEGER))
), cohort_grid AS (
    SELECT c.*, h.month_index,
           STRFTIME('%Y-%m', c.cohort_month || '-01', '+' || h.month_index || ' months') AS target_month,
           o.first_completed_month, o.last_completed_month
    FROM cohort_customers AS c CROSS JOIN cohort_horizon AS h CROSS JOIN customer_observation AS o
), cohort_coverage AS (
    SELECT g.*, CASE
        WHEN month_index = 0 THEN 'baseline_membership'
        WHEN target_month > last_completed_month THEN 'future_unobserved'
        WHEN target_month = last_completed_month THEN 'terminal_partial'
        WHEN COALESCE(m.all_orders, 0) = 0 THEN 'calendar_gap'
        ELSE 'interior_observed' END AS coverage_status,
        CASE WHEN target_month <= last_completed_month THEN COALESCE(a.observed_customers, 0) END AS observed_customers
    FROM cohort_grid AS g
    LEFT JOIN all_order_month_counts AS m ON m.month = g.target_month
    LEFT JOIN cohort_activity AS a ON a.cohort_month = g.cohort_month AND a.purchase_month = g.target_month
), cohort_matrix AS (
    SELECT cohort_month, new_customers, month_index, target_month, coverage_status,
           observed_customers,
           CASE WHEN coverage_status IN ('baseline_membership', 'interior_observed') THEN observed_customers END AS returning_customers_for_rate,
           CASE WHEN coverage_status IN ('baseline_membership', 'interior_observed') THEN 100 * observed_customers END AS retention_percent_numerator,
           new_customers AS retention_percent_denominator,
           CAST(coverage_status = 'future_unobserved' AS INTEGER) AS flag_future_unobserved,
           CAST(coverage_status = 'terminal_partial' AS INTEGER) AS flag_terminal_partial,
           CAST(coverage_status = 'calendar_gap' AS INTEGER) AS flag_calendar_gap
    FROM cohort_coverage
), cohort_followup AS (
    SELECT cohort_month,
           SUM(month_index > 0 AND coverage_status = 'interior_observed') AS available_interior_future_months,
           SUM(month_index BETWEEN 1 AND 3 AND coverage_status = 'interior_observed') AS covered_first_three_future_months,
           SUM(month_index >= 4 AND coverage_status = 'interior_observed') AS covered_month_4_plus
    FROM cohort_matrix GROUP BY cohort_month
), cohort_later_returns AS (
    SELECT a.cohort_month, COUNT(DISTINCT a.customer_unique_id) AS customers_returning_month_4_plus
    FROM customer_month_activity AS a JOIN cohort_matrix AS m
      ON m.cohort_month = a.cohort_month AND m.target_month = a.purchase_month
    WHERE m.month_index >= 4 AND m.coverage_status = 'interior_observed'
    GROUP BY a.cohort_month
)

-- Original cohort size is every rate denominator. Repeat includes same-month repeat
-- orders; retention in month k counts distinct customers purchasing in that later month.
SELECT c.cohort_month, c.new_customers, c.completed_orders, c.repeat_customers,
 c.item_sales_hundredths, c.freight_hundredths, c.items_purchased,
 c.item_sales_hundredths AS average_customer_sales_hundredths_numerator, c.new_customers AS average_customer_sales_hundredths_denominator,
 100*c.repeat_customers AS observed_repeat_rate_percent_numerator, c.new_customers AS observed_repeat_rate_percent_denominator,
 COALESCE(a.same_month_repeat_customers,0) AS same_month_repeat_customers,
 m1.returning_customers_for_rate AS customers_returning_month_1, m1.coverage_status AS month_1_coverage,
 m1.retention_percent_numerator AS month_1_retention_percent_numerator, c.new_customers AS month_1_retention_percent_denominator,
 m2.returning_customers_for_rate AS customers_returning_month_2, m2.coverage_status AS month_2_coverage,
 m2.retention_percent_numerator AS month_2_retention_percent_numerator, c.new_customers AS month_2_retention_percent_denominator,
 m3.returning_customers_for_rate AS customers_returning_month_3, m3.coverage_status AS month_3_coverage,
 m3.retention_percent_numerator AS month_3_retention_percent_numerator, c.new_customers AS month_3_retention_percent_denominator,
 CASE WHEN f.covered_month_4_plus>0 THEN COALESCE(l.customers_returning_month_4_plus,0) END AS customers_returning_month_4_plus,
 f.available_interior_future_months, CAST(f.covered_first_three_future_months<3 AS INTEGER) AS flag_insufficient_three_month_coverage,
 CAST(c.cohort_month=(SELECT first_completed_month FROM customer_observation) AS INTEGER) AS flag_initial_boundary_cohort,
 CAST(c.cohort_month=(SELECT last_completed_month FROM customer_observation) AS INTEGER) AS flag_terminal_boundary_cohort
FROM cohort_customers AS c JOIN cohort_followup AS f USING(cohort_month)
LEFT JOIN cohort_activity AS a ON a.cohort_month=c.cohort_month AND a.purchase_month=c.cohort_month
LEFT JOIN cohort_matrix AS m1 ON m1.cohort_month=c.cohort_month AND m1.month_index=1
LEFT JOIN cohort_matrix AS m2 ON m2.cohort_month=c.cohort_month AND m2.month_index=2
LEFT JOIN cohort_matrix AS m3 ON m3.cohort_month=c.cohort_month AND m3.month_index=3
LEFT JOIN cohort_later_returns AS l ON l.cohort_month=c.cohort_month ORDER BY c.cohort_month;

-- result: cohort_retention_long
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
-- Append to customer_level_aggregates.sql. Each customer enters one first-observed
-- completed-purchase cohort. Activity is deduplicated to customer/month BEFORE joins.
-- A cohort's original size is every retention denominator; month 0 is membership,
-- not repeat retention. Future/gap/terminal-partial rates are NULL, not zeros.
, cohort_customers AS (
    SELECT cohort_month, COUNT(*) AS new_customers,
           SUM(completed_order_count) AS completed_orders,
           SUM(repeat_customer_flag) AS repeat_customers,
           SUM(item_sales_hundredths) AS item_sales_hundredths,
           SUM(freight_hundredths) AS freight_hundredths,
           SUM(items_purchased) AS items_purchased
    FROM customer_level GROUP BY cohort_month
), customer_month_activity AS (
    SELECT c.cohort_month, p.customer_unique_id, p.purchase_month, COUNT(*) AS orders_in_month
    FROM completed_purchases AS p JOIN customer_level AS c USING(customer_unique_id)
    GROUP BY c.cohort_month, p.customer_unique_id, p.purchase_month
), cohort_activity AS (
    SELECT cohort_month, purchase_month, COUNT(*) AS observed_customers,
           SUM(orders_in_month >= 2 AND cohort_month = purchase_month) AS same_month_repeat_customers
    FROM customer_month_activity GROUP BY cohort_month, purchase_month
), all_order_month_counts AS (
    SELECT SUBSTR(order_purchase_timestamp, 1, 7) AS month, COUNT(*) AS all_orders
    FROM orders GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
), cohort_horizon(month_index) AS (
    SELECT 0 UNION ALL SELECT month_index + 1 FROM cohort_horizon, customer_observation
    WHERE month_index < MAX(3,
        12 * (CAST(SUBSTR(last_completed_month, 1, 4) AS INTEGER) - CAST(SUBSTR(first_completed_month, 1, 4) AS INTEGER))
        + CAST(SUBSTR(last_completed_month, 6, 2) AS INTEGER) - CAST(SUBSTR(first_completed_month, 6, 2) AS INTEGER))
), cohort_grid AS (
    SELECT c.*, h.month_index,
           STRFTIME('%Y-%m', c.cohort_month || '-01', '+' || h.month_index || ' months') AS target_month,
           o.first_completed_month, o.last_completed_month
    FROM cohort_customers AS c CROSS JOIN cohort_horizon AS h CROSS JOIN customer_observation AS o
), cohort_coverage AS (
    SELECT g.*, CASE
        WHEN month_index = 0 THEN 'baseline_membership'
        WHEN target_month > last_completed_month THEN 'future_unobserved'
        WHEN target_month = last_completed_month THEN 'terminal_partial'
        WHEN COALESCE(m.all_orders, 0) = 0 THEN 'calendar_gap'
        ELSE 'interior_observed' END AS coverage_status,
        CASE WHEN target_month <= last_completed_month THEN COALESCE(a.observed_customers, 0) END AS observed_customers
    FROM cohort_grid AS g
    LEFT JOIN all_order_month_counts AS m ON m.month = g.target_month
    LEFT JOIN cohort_activity AS a ON a.cohort_month = g.cohort_month AND a.purchase_month = g.target_month
), cohort_matrix AS (
    SELECT cohort_month, new_customers, month_index, target_month, coverage_status,
           observed_customers,
           CASE WHEN coverage_status IN ('baseline_membership', 'interior_observed') THEN observed_customers END AS returning_customers_for_rate,
           CASE WHEN coverage_status IN ('baseline_membership', 'interior_observed') THEN 100 * observed_customers END AS retention_percent_numerator,
           new_customers AS retention_percent_denominator,
           CAST(coverage_status = 'future_unobserved' AS INTEGER) AS flag_future_unobserved,
           CAST(coverage_status = 'terminal_partial' AS INTEGER) AS flag_terminal_partial,
           CAST(coverage_status = 'calendar_gap' AS INTEGER) AS flag_calendar_gap
    FROM cohort_coverage
), cohort_followup AS (
    SELECT cohort_month,
           SUM(month_index > 0 AND coverage_status = 'interior_observed') AS available_interior_future_months,
           SUM(month_index BETWEEN 1 AND 3 AND coverage_status = 'interior_observed') AS covered_first_three_future_months,
           SUM(month_index >= 4 AND coverage_status = 'interior_observed') AS covered_month_4_plus
    FROM cohort_matrix GROUP BY cohort_month
), cohort_later_returns AS (
    SELECT a.cohort_month, COUNT(DISTINCT a.customer_unique_id) AS customers_returning_month_4_plus
    FROM customer_month_activity AS a JOIN cohort_matrix AS m
      ON m.cohort_month = a.cohort_month AND m.target_month = a.purchase_month
    WHERE m.month_index >= 4 AND m.coverage_status = 'interior_observed'
    GROUP BY a.cohort_month
)

-- Long-form audit includes observed counts even for terminal partial/gap cells.
-- The exported wide matrix leaves unmeasured rates blank and carries cell coverage.
SELECT * FROM cohort_matrix ORDER BY cohort_month, month_index;
