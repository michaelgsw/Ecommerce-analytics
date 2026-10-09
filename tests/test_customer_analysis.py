"""Identity, censoring, timestamp ties, precision and category-grain boundaries."""

from contextlib import redirect_stdout
import io
import unittest

import test_analysis as base_fixture
from src.analysis.customer_queries import execute_customer_queries
from src.analysis.run_customer_analysis import retention_matrix
from src.analysis.validate_customer_analysis import validate_customer_analysis


class CustomerAnalysisTests(unittest.TestCase):
    def setUp(self):
        # Reuse the adversarial base-table fixture, not expected analytical results.
        self.fixture = base_fixture.AnalysisTests()
        self.fixture.setUp()
        self.db = self.fixture.db

    def tearDown(self):
        self.fixture.tearDown()

    def queries(self):
        with redirect_stdout(io.StringIO()):
            return execute_customer_queries(self.db)

    def prior(self):
        # The fixture has two delivered orders for one persistent customer.
        return {"unique_customers": 1, "customers_two_plus_completed_orders": 1,
                "completed_orders": 2, "item_sales_hundredths": self.fixture.large + 508}

    def test_customer_bridge_exact_money_and_conflicting_state(self):
        self.db.execute("UPDATE customers SET customer_state='other' WHERE customer_id='b'")
        results, prefix, _ = self.queries()
        row = self.db.execute(prefix + "SELECT * FROM customer_level").fetchone()
        self.assertEqual(row['customer_unique_id'], 'person-one')
        self.assertEqual(row['completed_order_count'], 2)
        self.assertEqual(row['item_sales_hundredths'], self.fixture.large + 508)
        self.assertIs(type(row['item_sales_hundredths']), int)
        self.assertEqual(row['average_order_value_hundredths'], f"{self.fixture.large + 508}/2")
        self.assertIsNone(row['customer_state'])
        self.assertEqual(row['days_between_first_and_last_purchase'], 59)
        self.assertEqual(row['observation_date'], '2018-03-15')
        self.assertEqual(row['recency_days'], 0)
        checks = validate_customer_analysis(self.db, results, prefix, self.prior())['checks']
        self.assertTrue(all(check['passed'] for check in checks))

    def test_cohort_gap_partial_future_and_baseline_are_distinct(self):
        results, _, _ = self.queries()
        cells = {r['month_index']: r for r in results['cohort_retention_long']}
        self.assertEqual(cells[0]['coverage_status'], 'baseline_membership')
        self.assertEqual(cells[0]['retention_percent_numerator'], 100)
        self.assertEqual(cells[1]['coverage_status'], 'calendar_gap')
        self.assertEqual(cells[1]['observed_customers'], 0)
        self.assertIsNone(cells[1]['retention_percent_numerator'])
        self.assertEqual(cells[2]['coverage_status'], 'terminal_partial')
        self.assertEqual(cells[2]['observed_customers'], 1)
        self.assertIsNone(cells[2]['returning_customers_for_rate'])
        self.assertEqual(cells[3]['coverage_status'], 'future_unobserved')
        self.assertIsNone(cells[3]['observed_customers'])
        wide = retention_matrix(results['cohort_retention_long'])[0]
        self.assertEqual(wide['new_customers'], 1)
        self.assertEqual(wide['month_0_retention_percent'], '100.000000')
        self.assertIsNone(wide['month_2_retention_percent'])
        # An interior month with observed all-status orders can measure zero returns.
        self.fixture.insert('orders', order_id='feb', customer_id='c', order_status='canceled',
                            order_purchase_timestamp='2018-02-01 10:00:00')
        results, _, _ = self.queries()
        february = next(r for r in results['cohort_retention_long'] if r['month_index'] == 1)
        self.assertEqual(february['coverage_status'], 'interior_observed')
        self.assertEqual(february['retention_percent_numerator'], 0)

    def test_same_timestamp_seconds_are_zero_days_and_flagged(self):
        self.db.execute("UPDATE orders SET order_purchase_timestamp='2018-01-15 12:00:00' WHERE order_id='o2'")
        results, prefix, _ = self.queries()
        timing = {r['metric']: r for r in results['repeat_purchase_summary']}
        self.assertEqual(timing['same_day_second_purchase']['count'], 1)
        self.assertEqual(timing['first_second_timestamp_ties']['count'], 1)
        self.assertEqual(timing['median_days_to_second_purchase']['value_numerator'], 0)
        second = self.db.execute(prefix + "SELECT order_id FROM ranked_purchases WHERE purchase_number=2").fetchone()
        self.assertEqual(second[0], 'o2')
        validate_customer_analysis(self.db, results, prefix, self.prior())

    def test_repeated_category_items_do_not_multiply_transitions(self):
        results, prefix, _ = self.queries()
        first = [r for r in results['category_transitions'] if r['scope'] == 'first_to_second']
        self.assertEqual(sum(r['order_transitions'] for r in first), 1)
        self.assertEqual(first[0]['behavior'], 'category_unknown')
        self.db.execute("UPDATE products SET product_category_name='untranslated' WHERE product_id='p2'")
        results, _, _ = self.queries()
        first = [r for r in results['category_transitions'] if r['scope'] == 'first_to_second']
        self.assertEqual(first[0]['order_transitions'], 1)
        self.assertEqual(first[0]['behavior'], 'same_category_set')
        category = results['category_customer_behavior'][0]
        self.assertEqual(category['completed_orders'], 2)
        self.assertEqual(category['items_purchased'], 3)
        self.assertEqual(category['item_sales_hundredths'], self.fixture.large + 508)

    def test_threshold_ties_remain_standard_and_no_binary_floats(self):
        results, prefix, _ = self.queries()
        # With one customer all quartiles equal their sales: equality is standard.
        row = self.db.execute(prefix + "SELECT * FROM customer_segments").fetchone()
        self.assertEqual(row['high_value_flag'], 0)
        self.assertEqual(row['segment'], 'Standard repeat')
        self.assertEqual(row['high_value_threshold_hundredths_numerator'], 2 * (self.fixture.large + 508))
        self.assertTrue(all(type(value) is not float for rows in results.values() for r in rows for value in r.values()))
        self.assertEqual(results['pareto_concentration'][-1]['item_sales_hundredths'], self.fixture.large + 508)

    def test_independent_validation_rejects_fanout_and_false_future_zero(self):
        results, prefix, _ = self.queries()
        results['customer_segments'][0]['completed_orders'] += 1
        with self.assertRaisesRegex(ValueError, 'segment'):
            validate_customer_analysis(self.db, results, prefix, self.prior())
        results, prefix, _ = self.queries()
        results['cohort_retention_long'][-1]['returning_customers_for_rate'] = 0
        with self.assertRaisesRegex(ValueError, 'retention cell'):
            validate_customer_analysis(self.db, results, prefix, self.prior())


if __name__ == '__main__':
    unittest.main()
