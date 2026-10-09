"""Integration checks require an actual completed pipeline run first."""

from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import unittest
from zipfile import ZipFile

from src.cleaning.schema import FILES, FOREIGN_KEYS, KEYS

ROOT = Path(__file__).resolve().parents[1]


class ProcessedOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest_path = ROOT / "data/processed/cleaning_manifest.json"
        if not manifest_path.exists():
            raise RuntimeError("Run python -m src.cleaning.run_cleaning before running the tests.")
        cls.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cls.tables = {}
        for name in FILES:
            with (ROOT / "data/processed" / f"{name}_clean.csv").open(encoding="utf-8", newline="") as source:
                cls.tables[name] = list(csv.DictReader(source))

    def test_original_csv_bytes_match_downloaded_archive(self):
        with ZipFile(ROOT / "data/raw/olist_brazilian_ecommerce.zip") as archive:
            for entry in archive.infolist():
                with self.subTest(file=entry.filename):
                    with archive.open(entry) as original:
                        expected = hashlib.file_digest(original, "sha256").hexdigest()
                    with (ROOT / "data/raw" / entry.filename).open("rb") as current:
                        self.assertEqual(hashlib.file_digest(current, "sha256").hexdigest(), expected)

    def test_processed_counts_and_hashes_match_manifest(self):
        for name, rows in self.tables.items():
            with self.subTest(table=name):
                details = self.manifest["tables"][name]
                self.assertEqual(len(rows), details["processed_rows"])
                self.assertEqual(len(rows), details["original_rows"] - details["duplicates_removed"])
                with (ROOT / "data/processed" / f"{name}_clean.csv").open("rb") as source:
                    self.assertEqual(hashlib.file_digest(source, "sha256").hexdigest(), details["output_sha256"])

    def test_all_prepared_keys_are_unique_and_complete(self):
        for name, rows in self.tables.items():
            with self.subTest(table=name):
                keys = [tuple(row[column] for column in KEYS[name]) for row in rows]
                self.assertEqual(len(keys), len(set(keys)))
                self.assertTrue(all(all(key) for key in keys))

    def test_required_foreign_keys_and_customer_identity(self):
        for child, child_column, parent, parent_column in FOREIGN_KEYS:
            parent_values = {row[parent_column] for row in self.tables[parent]}
            with self.subTest(child=child, column=child_column):
                self.assertTrue(all(row[child_column] in parent_values for row in self.tables[child]))
        customers = self.tables["customers"]
        orders = self.tables["orders"]
        self.assertEqual({row["customer_id"] for row in customers}, {row["customer_id"] for row in orders})
        self.assertEqual(len(orders), len({row["customer_id"] for row in orders}))
        # Ensure the processed persistent-ID distribution matches the real source.
        with (ROOT / "data/raw" / FILES["customers"]).open(encoding="utf-8", newline="") as source:
            source_ids = Counter(row["customer_unique_id"] for row in csv.DictReader(source))
        self.assertEqual(source_ids, Counter(row["customer_unique_id"] for row in customers))

    def test_serialized_prices_and_freight_are_nonnegative_decimals(self):
        for row in self.tables["order_items"]:
            for column in ["price", "freight_value"]:
                value = Decimal(row[column])
                self.assertTrue(value.is_finite() and value >= 0)

    def test_manifest_has_no_failed_required_checks(self):
        self.assertTrue(self.manifest["raw_files_unchanged"])
        self.assertTrue(self.manifest["checks"])
        self.assertTrue(all(check["passed"] for check in self.manifest["checks"]))


if __name__ == "__main__":
    unittest.main()
