"""Adversarial grain, identity, precision, and coverage tests for business SQL."""

from contextlib import redirect_stdout
from decimal import Decimal
import io
from pathlib import Path
import sqlite3
import unittest

from src.analysis.run_analysis import add_decimal_displays, decimal_ratio, execute_queries
from src.analysis.validate_metrics import validate_metrics

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
        for label, person in (("a", "person-one"), ("b", "person-one"), ("c", "person-two"), ("d", "person-three")):
            self.insert("customers", customer_id=label, customer_unique_id=person)
        for key, customer, status, month in (("o1", "a", "delivered", "01"), ("o2", "b", "delivered", "03"), ("o3", "c", "canceled", "01"), ("o4", "d", "unavailable", "04")):
            self.insert("orders", order_id=key, customer_id=customer, order_status=status, order_purchase_timestamp=f"2018-{month}-15 12:00:00")
        self.insert("product_categories", product_category_name="untranslated")
        self.insert("products", product_id="p1", product_category_name="untranslated")
        self.insert("products", product_id="p2")
        self.insert("sellers", seller_id="seller")
        # Above 2**53: binary float would lose one hundredth.
        self.large = 9007199254740993
        for order, sequence, product, price, freight in (("o1", 1, "p1", self.large, 0), ("o1", 2, "p1", 7, 0), ("o2", 1, "p2", 501, 23), ("o3", 1, "p1", 99, 0)):
            self.insert("order_items", order_id=order, order_item_id=sequence, product_id=product, seller_id="seller", price=str(Decimal(price) / 100), price_hundredths=price, freight_value=str(Decimal(freight) / 100), freight_value_hundredths=freight)
        for order, sequence, amount in (("o1", 1, self.large), ("o1", 2, 7), ("o1", 3, 11), ("o2", 1, 504), ("o3", 1, 0), ("o4", 1, 100)):
            self.insert("payments", order_id=order, payment_sequential=sequence, payment_type="voucher", payment_value=str(Decimal(amount) / 100), payment_value_hundredths=amount)
        for review, order, score in (("reused", "o1", 5), ("second", "o1", 1), ("reused", "o2", 4)):
            self.insert("reviews", review_id=review, order_id=order, review_score=score)

    def tearDown(self):
        self.db.close()

    def insert(self, table, **changes):
        values = {}
        for row in self.db.execute(f"PRAGMA table_info({table})"):
            name = row["name"]
            if not row["notnull"]:
                values[name] = None
            elif name.startswith("flag_"):
                values[name] = 0
            elif row["type"] == "INTEGER":
                values[name] = 1
            elif name in ("order_purchase_timestamp", "order_estimated_delivery_date", "shipping_limit_date", "review_creation_date", "review_answer_timestamp"):
                values[name] = "2018-01-15 12:00:00"
            else:
                values[name] = "fixture"
        values.update(changes)
        self.db.execute(f"INSERT INTO {table} ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})", tuple(values.values()))

    def queries(self):
        with redirect_stdout(io.StringIO()):
            return execute_queries(self.db)

    def test_multiple_children_do_not_multiply_sales_or_persistent_customers(self):
        results, shared, _ = self.queries()
        overview = results["sales_overview"][0]
        self.assertEqual(overview["completed_orders"], 2)
        self.assertEqual(overview["items_sold"], 3)
        self.assertEqual(overview["item_sales_hundredths"], self.large + 508)
        self.assertIs(type(overview["item_sales_hundredths"]), int)
        self.assertEqual(overview["distinct_customers"], 1)
        self.assertEqual(results["customer_overview"][0]["customers_two_plus_completed_orders"], 1)
        review = dict(self.db.execute(shared + "\nSELECT * FROM review_summary WHERE order_id='o1'").fetchone())
        self.assertEqual(review["review_count"], 2)
        self.assertEqual(review["average_review_score"], "6/2")
        self.assertTrue(all(not isinstance(value, float) for rows in results.values() for row in rows for value in row.values()))

    def test_missing_and_untranslated_categories_and_status_denominator_survive(self):
        results, _, _ = self.queries()
        categories = {row["product_category_name"]: row for row in results["category_performance"]}
        self.assertEqual(categories[None]["item_sales_hundredths"], 501)
        self.assertEqual(categories[None]["flag_category_missing"], 1)
        self.assertEqual(categories["untranslated"]["flag_translation_missing"], 1)
        status = {row["order_status"]: row for row in results["order_status_summary"]}
        self.assertEqual(status["canceled"]["cancellation_rate_percent_numerator"], 100)
        self.assertEqual(status["canceled"]["cancellation_rate_percent_denominator"], 4)
        self.assertEqual(status["unavailable"]["orders_missing_items"], 1)

    def test_calendar_gap_and_boundary_comparisons_are_explicit(self):
        results, _, _ = self.queries()
        months = {row["month"]: row for row in results["monthly_sales"]}
        self.assertEqual(list(months), ["2018-01", "2018-02", "2018-03", "2018-04"])
        self.assertEqual(months["2018-02"]["completed_orders"], 0)
        self.assertEqual(months["2018-02"]["flag_no_observed_orders"], 1)
        self.assertEqual(months["2018-04"]["flag_extract_boundary_month"], 1)
        self.assertEqual(months["2018-03"]["flag_completed_sales_boundary_month"], 1)
        self.assertIsNone(months["2018-03"]["item_sales_mom_percent_numerator"])
        self.assertIsNone(months["2018-04"]["item_sales_mom_percent_denominator"])

    def test_independent_validator_rejects_changed_metrics(self):
        results, shared, _ = self.queries()
        findings = validate_metrics(self.db, results, shared)
        self.assertTrue(all(check["passed"] for check in findings["checks"]))
        results["sales_overview"][0]["item_sales_hundredths"] += 1
        with self.assertRaisesRegex(ValueError, "Sales overview"):
            validate_metrics(self.db, results, shared)

    def test_decimal_display_retains_rational_pair_and_undefined_values(self):
        self.assertEqual(decimal_ratio(1, 3), "0.333333")
        self.assertIsNone(decimal_ratio(1, 0))
        self.assertIsNone(decimal_ratio(None, None))
        source = [{"mean_numerator": self.large, "mean_denominator": 1}]
        result = add_decimal_displays(source)[0]
        self.assertEqual(result["mean"], "9007199254740993.000000")
        self.assertEqual(result["mean_numerator"], self.large)


if __name__ == "__main__":
    unittest.main()
