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
