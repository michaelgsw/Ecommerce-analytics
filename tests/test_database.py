"""Boundary tests for exact amounts and the approved relational constraints."""

import csv
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from src.database import build_database as builder
from src.database import validate_database as validator
from src.database.build_database import convert_value, scaled_hundredths

ROOT = Path(__file__).resolve().parents[1]


class StorageTests(unittest.TestCase):
    def test_exact_scale_and_zero_without_binary_float(self):
        for text, expected in (("0.00", 0), ("0.29", 29), ("13664.08", 1366408), ("1.2300", 123)):
            with self.subTest(value=text):
                self.assertEqual(scaled_hundredths(text), expected)

    def test_lossy_or_invalid_amounts_are_rejected(self):
        for text in ("0.001", "NaN", "Infinity", "-0.01", "bad", "92233720368547758.08"):
            with self.subTest(value=text), self.assertRaises(ValueError):
                scaled_hundredths(text)

    def test_source_text_and_nullable_timestamps(self):
        self.assertIsNone(convert_value("order_approved_at", ""))
        self.assertEqual(convert_value("customer_zip_code_prefix", "00123"), "00123")
        self.assertEqual(convert_value("review_comment_message", "  useful\nreview  "), "  useful\nreview  ")
        self.assertEqual(convert_value("order_purchase_timestamp", "2018-01-02 03:04:05"), "2018-01-02 03:04:05")
        for value in ("2018-02-30 03:04:05", "2018-1-2 03:04:05", "2018-01-02T03:04:05Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                convert_value("order_purchase_timestamp", value)


class ConstraintTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
        self.insert("customers", customer_id="customer-a", customer_unique_id="person-a")
        self.insert("customers", customer_id="customer-b", customer_unique_id="person-a")
        self.insert("orders", order_id="order-a", customer_id="customer-a", order_status="canceled")
        self.insert("orders", order_id="order-b", customer_id="customer-b", order_status="unavailable")

    def tearDown(self):
        self.db.close()

    def insert(self, table, **changes):
        """Supply simple fixture defaults for required columns; optional fields stay NULL."""
        values = {}
        for _, name, kind, required, _, _ in self.db.execute(f"PRAGMA table_info({table})"):
            if not required:
                values[name] = None
            elif name.startswith("flag_"):
                values[name] = 0
            elif kind == "INTEGER":
                values[name] = 1
            elif name in ("order_purchase_timestamp", "order_estimated_delivery_date", "shipping_limit_date", "review_creation_date", "review_answer_timestamp"):
                values[name] = "2018-01-02 03:04:05"
            else:
                values[name] = "fixture"
        values.update(changes)
        sql = f"INSERT INTO {table} ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})"
        self.db.execute(sql, tuple(values.values()))

    def test_optional_children_missing_dates_and_repeated_customer_identity(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM orders WHERE order_approved_at IS NULL").fetchone()[0], 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM customers WHERE customer_unique_id='person-a'").fetchone()[0], 2)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_multiple_payments_and_zero_edge_cases(self):
        self.insert("payments", order_id="order-a", payment_sequential=1, payment_type="not_defined", payment_installments=0, payment_value="0.00", payment_value_hundredths=0)
        self.insert("payments", order_id="order-a", payment_sequential=2, payment_type="voucher", payment_value="0.00", payment_value_hundredths=0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM payments").fetchone()[0], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert("payments", order_id="order-a", payment_sequential=2, payment_type="voucher")

    def test_reused_review_id_multiple_reviews_and_imperfect_chronology(self):
        self.insert("reviews", review_id="review-a", order_id="order-a", review_creation_date="2017-01-01 00:00:00")
        self.insert("reviews", review_id="review-a", order_id="order-b")
        self.insert("reviews", review_id="review-b", order_id="order-a")
        self.db.execute("UPDATE orders SET order_delivered_carrier_date = '2016-01-01 00:00:00'")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0], 3)
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert("reviews", review_id="review-a", order_id="order-a")

    def test_missing_categories_untranslated_labels_zero_weight_and_freight(self):
        self.insert("product_categories", product_category_name="untranslated")
        self.insert("products", product_id="product-a", product_category_name="untranslated", product_weight_g=0)
        self.insert("products", product_id="product-b")
        self.insert("sellers", seller_id="seller-a")
        self.insert("order_items", order_id="order-a", product_id="product-a", seller_id="seller-a", price="0.85", price_hundredths=85, freight_value="0.00", freight_value_hundredths=0)
        self.assertIsNone(self.db.execute("SELECT product_category_name_english FROM product_categories").fetchone()[0])
        self.assertIsNone(self.db.execute("SELECT product_category_name FROM products WHERE product_id='product-b'").fetchone()[0])

    def test_foreign_keys_null_primary_keys_and_valid_domains_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert("orders", order_id="orphan", customer_id="absent", order_status="created")
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert("customers", customer_id=None)
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert("reviews", review_id="invalid-score", order_id="order-a", review_score=6)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE orders SET flag_items_missing=2")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE customers SET source_record_number='not an integer'")


class PublicationAndValidationTests(unittest.TestCase):
    def test_failed_build_keeps_previous_database_and_removes_temporary_file(self):
        manifest = json.loads((ROOT / "data/processed/cleaning_manifest.json").read_text(encoding="utf-8"))
        hashes = {f"data/processed/{table}_clean.csv": detail["output_sha256"] for table, detail in manifest["tables"].items()}
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            destination = Path(folder) / "olist_analytics.db"
            original_bytes = b"previous database remains untouched"
            destination.write_bytes(original_bytes)
            with patch.object(builder, "DATABASE", destination), patch.object(builder, "protected_hashes", return_value=hashes), patch.object(builder, "stage_csv", side_effect=ValueError("fixture load failure")):
                with self.assertRaisesRegex(ValueError, "fixture load failure"):
                    builder.build_database()
            self.assertEqual(destination.read_bytes(), original_bytes)
            self.assertEqual(list(Path(folder).iterdir()), [destination])

    def test_independent_validator_detects_row_changes_despite_unchanged_counts(self):
        columns = ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state", "source_record_number", "source_file", "flag_geolocation_missing"]
        rows = [
            ["a", "same-person", "00123", "first-city", "SP", "1", "customers.csv", "False"],
            ["b", "same-person", "00456", "second-city", "SP", "2", "customers.csv", "True"],
        ]
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            temporary_root = Path(folder)
            prepared = temporary_root / "data/processed"
            prepared.mkdir(parents=True)
            with (prepared / "customers_clean.csv").open("w", encoding="utf-8", newline="") as output:
                writer = csv.writer(output)
                writer.writerow(columns)
                writer.writerows(rows)
            connection = sqlite3.connect(":memory:")
            connection.row_factory = sqlite3.Row
            try:
                connection.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
                for row in rows:
                    connection.execute("INSERT INTO stg_customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row)
                    converted = row[:5] + [int(row[5]), row[6], int(row[7] == "True")]
                    connection.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)", converted)
                # Swap two text values: counts, keys, NULLs, and text distributions all match.
                connection.execute("UPDATE customers SET customer_city = CASE customer_id WHEN 'a' THEN 'second-city' ELSE 'first-city' END")
                findings = {"checks": [], "tables": {}}
                with patch.object(validator, "ROOT", temporary_root):
                    validator.reconcile_table(connection, "customers", findings)
                failed = [check for check in findings["checks"] if not check["passed"]]
                self.assertEqual(len(failed), 1)
                self.assertEqual(failed[0]["name"], "customers: every prepared field and storage type")
                self.assertEqual(failed[0]["detail"]["mismatches"], 2)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
