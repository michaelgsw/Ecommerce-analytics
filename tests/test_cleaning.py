"""Boundary cases modify in-memory copies only; they are not analytical findings."""

from decimal import Decimal
import importlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from src.cleaning.common import prepare_frame
from src.cleaning.schema import FILES
from src.cleaning.run_cleaning import run_pipeline
from src.cleaning.validation import validate_relationships, validate_table

ROOT = Path(__file__).resolve().parents[1]


def fixture(name, rows=2):
    return pd.read_csv(ROOT / "data" / "raw" / FILES[name], nrows=rows, dtype="string", keep_default_na=False, encoding="utf-8-sig")


def clean_fixture(name, raw):
    frame, details = prepare_frame(raw)
    frame = importlib.import_module(f"src.cleaning.{name}").clean(frame)
    return frame, details


class CleaningBoundaryTests(unittest.TestCase):
    def test_only_identical_rows_are_removed_with_lineage(self):
        raw = fixture("customers", 1)
        duplicate = pd.concat([raw, raw], ignore_index=True)
        frame, details = clean_fixture("customers", duplicate)
        self.assertEqual(len(frame), 1)
        self.assertEqual(details["duplicates_removed"], 1)
        self.assertEqual(details["removed_source_record_numbers"], [2])
        self.assertEqual(frame["source_record_number"].tolist(), [1])

    def test_persistent_customer_id_is_not_a_deduplication_key(self):
        raw = fixture("customers")
        raw.loc[1, "customer_unique_id"] = raw.loc[0, "customer_unique_id"]
        frame, details = clean_fixture("customers", raw)
        validate_table("customers", frame, details)
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame["customer_id"].nunique(), 2)
        self.assertEqual(frame["customer_unique_id"].nunique(), 1)

    def test_postal_prefix_leading_zeros_survive(self):
        raw = fixture("customers", 1)
        raw.loc[0, "customer_zip_code_prefix"] = "00123"
        frame, details = clean_fixture("customers", raw)
        validate_table("customers", frame, details)
        self.assertEqual(frame.loc[0, "customer_zip_code_prefix"], "00123")

    def test_blank_comments_are_missing_but_literal_na_is_preserved(self):
        raw = fixture("reviews")
        raw.loc[0, "review_comment_message"] = " \n\t "
        raw.loc[1, "review_comment_message"] = "NA"
        frame, _ = clean_fixture("reviews", raw)
        self.assertTrue(pd.isna(frame.loc[0, "review_comment_message"]))
        self.assertEqual(frame.loc[1, "review_comment_message"], "NA")

    def test_populated_review_text_is_preserved_verbatim(self):
        raw = fixture("reviews", 1)
        text = "  Ótimo produto!\nSegunda linha.  "
        raw.loc[0, "review_comment_message"] = text
        frame, _ = clean_fixture("reviews", raw)
        self.assertEqual(frame.loc[0, "review_comment_message"], text)

    def test_reused_review_id_under_different_orders_is_retained(self):
        raw = fixture("reviews")
        raw.loc[1, "review_id"] = raw.loc[0, "review_id"]
        frame, details = clean_fixture("reviews", raw)
        validate_table("reviews", frame, details)
        self.assertEqual(len(frame), 2)

    def test_conflicting_review_composite_key_stops_validation(self):
        raw = fixture("reviews")
        raw.loc[1, ["review_id", "order_id"]] = raw.loc[0, ["review_id", "order_id"]]
        raw.loc[1, "review_score"] = "1" if raw.loc[0, "review_score"] != "1" else "5"
        frame, details = clean_fixture("reviews", raw)
        with self.assertRaisesRegex(ValueError, "unique key"):
            validate_table("reviews", frame, details)

    def test_conflicting_order_key_is_not_silently_dropped(self):
        raw = fixture("orders")
        raw.loc[1, "order_id"] = raw.loc[0, "order_id"]
        frame, details = clean_fixture("orders", raw)
        self.assertEqual(len(frame), 2)
        with self.assertRaisesRegex(ValueError, "unique key"):
            validate_table("orders", frame, details)

    def test_negative_price_is_rejected(self):
        raw = fixture("order_items", 1)
        raw.loc[0, "price"] = "-0.01"
        with self.assertRaisesRegex(ValueError, "negative"):
            clean_fixture("order_items", raw)

    def test_negative_freight_is_rejected(self):
        raw = fixture("order_items", 1)
        raw.loc[0, "freight_value"] = "-1"
        with self.assertRaisesRegex(ValueError, "negative"):
            clean_fixture("order_items", raw)

    def test_nonfinite_money_is_rejected(self):
        raw = fixture("payments", 1)
        raw.loc[0, "payment_value"] = "Infinity"
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            clean_fixture("payments", raw)

    def test_decimal_precision_and_zero_freight_are_preserved(self):
        raw = fixture("order_items", 1)
        raw.loc[0, "price"] = "0.100000000000000001"
        raw.loc[0, "freight_value"] = "0.00"
        frame, details = clean_fixture("order_items", raw)
        validate_table("order_items", frame, details)
        self.assertEqual(frame.loc[0, "price"], Decimal("0.100000000000000001"))
        self.assertEqual(frame.loc[0, "freight_value"], Decimal("0.00"))

    def test_missing_required_price_stops_validation(self):
        raw = fixture("order_items", 1)
        raw.loc[0, "price"] = ""
        frame, details = clean_fixture("order_items", raw)
        with self.assertRaisesRegex(ValueError, "required fields populated"):
            validate_table("order_items", frame, details)

    def test_invalid_nonmissing_timestamp_is_rejected(self):
        raw = fixture("orders", 1)
        raw.loc[0, "order_approved_at"] = "2018-02-30 12:00:00"
        with self.assertRaisesRegex(ValueError, "invalid nonmissing timestamps"):
            clean_fixture("orders", raw)

    def test_missing_optional_dates_are_not_imputed(self):
        raw = fixture("orders", 1)
        raw.loc[0, "order_approved_at"] = ""
        frame, details = clean_fixture("orders", raw)
        validate_table("orders", frame, details)
        self.assertTrue(pd.isna(frame.loc[0, "order_approved_at"]))

    def test_chronology_conflict_is_flagged_and_retained(self):
        raw = fixture("orders", 1)
        purchase = pd.Timestamp(raw.loc[0, "order_purchase_timestamp"])
        raw.loc[0, "order_delivered_carrier_date"] = str(purchase - pd.Timedelta(days=1))
        frame, details = clean_fixture("orders", raw)
        validate_table("orders", frame, details)
        self.assertTrue(frame.loc[0, "flag_carrier_before_purchase"])
        self.assertEqual(len(frame), 1)

    def test_unrecognized_order_status_is_rejected(self):
        raw = fixture("orders", 1)
        raw.loc[0, "order_status"] = "unexpected_status"
        frame, details = clean_fixture("orders", raw)
        with self.assertRaisesRegex(ValueError, "recognized statuses"):
            validate_table("orders", frame, details)

    def test_invalid_identifier_is_rejected(self):
        raw = fixture("customers", 1)
        raw.loc[0, "customer_id"] = "invalid"
        frame, details = clean_fixture("customers", raw)
        with self.assertRaisesRegex(ValueError, "valid identifiers"):
            validate_table("customers", frame, details)

    def test_nullable_product_metadata_and_column_mapping(self):
        raw = fixture("products", 1)
        raw.loc[0, "product_name_lenght"] = ""
        raw.loc[0, "product_category_name"] = "  Casa E Jardim  "
        frame, details = clean_fixture("products", raw)
        validate_table("products", frame, details)
        self.assertTrue(pd.isna(frame.loc[0, "product_name_length"]))
        self.assertEqual(frame.loc[0, "product_category_name"], "casa_e_jardim")
        self.assertNotIn("product_name_lenght", frame)

    def test_fractional_integer_is_rejected(self):
        raw = fixture("products", 1)
        raw.loc[0, "product_photos_qty"] = "1.5"
        with self.assertRaisesRegex(ValueError, "whole-number"):
            clean_fixture("products", raw)

    def test_duplicate_normalized_column_names_are_rejected(self):
        frame = pd.DataFrame([["a", "b"]], columns=["Name", " name "])
        with self.assertRaisesRegex(ValueError, "Ambiguous column"):
            prepare_frame(frame)

    def test_orphan_foreign_key_is_rejected(self):
        # Use small in-memory key sets solely to exercise the relationship guard.
        tables = {
            "customers": pd.DataFrame({"customer_id": ["known"]}),
            "orders": pd.DataFrame({"customer_id": ["missing"]}),
        }
        with self.assertRaisesRegex(ValueError, "references customers"):
            validate_relationships(tables)

    def test_failed_validation_preserves_previous_outputs(self):
        # Mock input reads; no CSV is created or modified in any raw directory.
        inputs = {name: fixture(name, 1) for name in FILES}
        inputs["order_items"].loc[0, "price"] = "-0.01"
        temporary_parent = ROOT / ".venv" / "tmp"
        temporary_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_parent) as temporary:
            test_root = Path(temporary)
            (test_root / "data/raw").mkdir(parents=True)
            processed = test_root / "data/processed"
            processed.mkdir()
            previous = processed / "customers_clean.csv"
            previous.write_text("previous validated output", encoding="utf-8")

            def mocked_read(path, **kwargs):
                name = next(name for name, filename in FILES.items() if filename == path.name)
                return inputs[name].copy()

            with patch("src.cleaning.run_cleaning.PROJECT_ROOT", test_root):
                with patch("src.cleaning.run_cleaning.pd.read_csv", side_effect=mocked_read):
                    with self.assertRaisesRegex(ValueError, "negative"):
                        run_pipeline(overwrite=True)
            self.assertEqual(previous.read_text(encoding="utf-8"), "previous validated output")
            self.assertFalse((processed / "cleaning_manifest.json").exists())
            self.assertFalse((test_root / "reports/cleaning_report.md").exists())
            self.assertEqual(list((test_root / "data/raw").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
