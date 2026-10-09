"""Dashboard handoff tests: corruption, NULL coverage, mixed scopes and precision."""

import copy
import json
from pathlib import Path
import unittest

from src.dashboard.build_dashboard_data import table_contract
from src.dashboard.prepare import kpis, prepare_tables
from src.dashboard.validate import validate_tables

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.business = json.loads((ROOT / 'reports/business_metric_validation.json').read_text(encoding='utf-8'))['results']
        cls.customer = json.loads((ROOT / 'reports/customer_analysis_validation.json').read_text(encoding='utf-8'))['results']

    def setUp(self):
        self.tables = prepare_tables(self.business, self.customer)

    def test_full_handoff_reconciles_to_previous_independent_evidence(self):
        evidence = validate_tables(self.tables, self.business, self.customer)
        self.assertTrue(all(row['passed'] for row in evidence['checks']))
        self.assertEqual(evidence['control_totals']['customers'], 93358)
        self.assertEqual(sum(r['item_sales_hundredths'] for r in self.tables['dashboard_categories']
                             if r['customer_type'] == 'All completed'), 1322149811)

    def test_false_future_zero_is_rejected_and_measured_zero_is_preserved(self):
        cells = self.tables['dashboard_cohorts']
        zero = next(r for r in cells if r['cohort_month'] == '2016-09' and r['month_index'] == 1)
        future = next(r for r in cells if r['cohort_month'] == '2018-08' and r['month_index'] == 1)
        self.assertEqual(zero['retention_percent_numerator'], 0)
        self.assertIsNone(future['retention_percent_numerator'])
        future['retention_percent_numerator'] = 0
        with self.assertRaisesRegex(ValueError, 'NULL'):
            validate_tables(self.tables, self.business, self.customer)

    def test_customer_fanout_and_altered_denominators_are_rejected(self):
        self.tables['dashboard_customer_segments'].append(copy.deepcopy(self.tables['dashboard_customer_segments'][0]))
        with self.assertRaisesRegex(ValueError, 'Segment customer/order/sales totals'):
            validate_tables(self.tables, self.business, self.customer)
        self.tables = prepare_tables(self.business, self.customer)
        self.tables['dashboard_categories'][0]['sales_share_percent_denominator'] = self.tables['dashboard_categories'][0]['item_sales_hundredths']
        with self.assertRaisesRegex(ValueError, 'fixed full-group denominator'):
            validate_tables(self.tables, self.business, self.customer)

    def test_missing_translations_and_source_categories_are_not_invented(self):
        category = next(r for r in self.tables['dashboard_categories'] if r['flag_translation_missing'])
        self.assertIsNone(category['product_category_name_english'])
        category['product_category_name_english'] = 'invented translation'
        with self.assertRaisesRegex(ValueError, 'translation flag'):
            validate_tables(self.tables, self.business, self.customer)

    def test_large_integer_kpi_and_powerbi_contract_avoid_decimal_coercion(self):
        source = copy.deepcopy(self.business)
        large = 9007199254740993
        source['sales_overview'][0]['item_sales_hundredths'] = large
        source['sales_overview'][0]['average_order_value_hundredths_numerator'] = large
        source['sales_overview'][0]['average_order_value_hundredths_denominator'] = 3
        rows = kpis(source)
        sales = next(row for row in rows if row['metric_key'] == 'observed_item_sales')
        self.assertIs(type(sales['numerator']), int)
        self.assertEqual(sales['display_value_text'], str(large))
        mean = next(row for row in rows if row['metric_key'] == 'average_order_value')
        self.assertEqual(mean['display_value_text'], '3002399751580331.000000')
        types = {field['name']: field for field in table_contract(rows)}
        self.assertEqual(types['numerator']['powerbi_type'], 'Whole number')
        self.assertEqual(types['display_value_text']['powerbi_type'], 'Text')
        self.assertEqual(types['completed_window_end_date']['powerbi_type'], 'Date')


if __name__ == '__main__':
    unittest.main()
