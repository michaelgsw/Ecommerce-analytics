"""Inspect the raw Olist CSV files without changing or cleaning them.

Run from the project root: python src/profile_data.py
Use --overwrite to intentionally regenerate the local JSON profile.
"""

import argparse
import hashlib
import json
import platform
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "data_profile.json"

FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

KEYS = {
    "customers": [["customer_id"], ["customer_unique_id"]],
    "geolocation": [["geolocation_zip_code_prefix"]],
    "order_items": [["order_id", "order_item_id"]],
    "order_payments": [["order_id", "payment_sequential"]],
    "order_reviews": [["review_id"], ["order_id"], ["review_id", "order_id"]],
    "orders": [["order_id"], ["customer_id"]],
    "products": [["product_id"]],
    "sellers": [["seller_id"]],
    "category_translation": [["product_category_name"], ["product_category_name_english"]],
}

DATE_COLUMNS = {
    "shipping_limit_date", "review_creation_date", "review_answer_timestamp",
    "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
}
NUMERIC_COLUMNS = {
    "geolocation_lat", "geolocation_lng", "order_item_id", "price", "freight_value",
    "payment_sequential", "payment_installments", "payment_value", "review_score",
    "product_name_lenght", "product_description_lenght", "product_photos_qty",
    "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
}
DECIMAL_COLUMNS = {
    "geolocation_lat", "geolocation_lng", "price", "freight_value", "payment_value",
}

# Each relationship is child table/column followed by parent table/column.
RELATIONSHIPS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("order_payments", "order_id", "orders", "order_id"),
    ("order_reviews", "order_id", "orders", "order_id"),
    ("products", "product_category_name", "category_translation", "product_category_name"),
    ("customers", "customer_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
    ("sellers", "seller_zip_code_prefix", "geolocation", "geolocation_zip_code_prefix"),
]


def file_hash(path):
    """Read in small blocks so hashing does not load another full file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def missing_mask(values):
    # Whitespace-only fields count as missing; literal strings such as 'NA' do not.
    return values.str.strip().eq("")


def profile_column(values, name):
    missing = missing_mask(values)
    present = values[~missing]
    result = {
        "inferred_type": "TEXT",
        "missing": int(missing.sum()),
        "empty_fields": int(values.eq("").sum()),
        "whitespace_only_fields": int((missing & values.ne("")).sum()),
        "surrounding_whitespace": int((~missing & values.ne(values.str.strip())).sum()),
        "distinct_nonmissing": int(present.nunique()),
    }
    if name in DATE_COLUMNS:
        dates = pd.to_datetime(present, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        result.update({
            "inferred_type": "TIMESTAMP (timezone unspecified)",
            "invalid_nonmissing": int(dates.isna().sum()),
            "minimum": None if dates.notna().sum() == 0 else str(dates.min()),
            "maximum": None if dates.notna().sum() == 0 else str(dates.max()),
        })
    elif name in NUMERIC_COLUMNS:
        numbers = pd.to_numeric(present, errors="coerce")
        valid = numbers.dropna()
        integer_values = bool(valid.mod(1).eq(0).all())
        logical_type = "DECIMAL" if name in DECIMAL_COLUMNS else "INTEGER"
        result.update({
            "inferred_type": logical_type,
            "invalid_nonmissing": int(numbers.isna().sum()),
            "non_integer_values": int(valid.mod(1).ne(0).sum()),
            "minimum": None if valid.empty else float(valid.min()),
            "maximum": None if valid.empty else float(valid.max()),
            "zero_values": int(valid.eq(0).sum()),
            "negative_values": int(valid.lt(0).sum()),
        })
        if logical_type == "INTEGER" and not integer_values:
            result["inferred_type"] = "DECIMAL (expected integer; investigate)"
    if name.endswith("_zip_code_prefix"):
        result["inferred_type"] = "TEXT (five-digit postal prefix)"
        result["invalid_format"] = int((~present.str.fullmatch(r"\d{5}")).sum())
        result["leading_zero_values"] = int(present.str.startswith("0").sum())
    elif name.endswith("_id") and name != "order_item_id":
        result["invalid_identifier_format"] = int((~present.str.fullmatch(r"[0-9a-f]{32}")).sum())
    return result


def profile_key(frame, columns):
    missing_rows = frame[columns].apply(missing_mask).any(axis=1)
    present = frame.loc[~missing_rows, columns]
    duplicates = int(present.duplicated().sum())
    return {
        "columns": columns,
        "missing_key_rows": int(missing_rows.sum()),
        "distinct_keys": int(len(present.drop_duplicates())),
        "duplicate_excess_rows": duplicates,
        "rows_in_repeated_keys": int(present.duplicated(keep=False).sum()),
        "unique_and_complete": bool(not missing_rows.any() and duplicates == 0),
    }


def profile_relationship(tables, child_name, child_column, parent_name, parent_column):
    child = tables[child_name][child_column]
    parent = tables[parent_name][parent_column]
    child_present = child[~missing_mask(child)]
    parent_present = parent[~missing_mask(parent)]
    unmatched = child_present[~child_present.isin(parent_present)]
    repeated_parent = parent_present.duplicated().any()
    return {
        "child": f"{child_name}.{child_column}",
        "parent": f"{parent_name}.{parent_column}",
        "missing_child_values": int(missing_mask(child).sum()),
        "unmatched_child_rows": int(len(unmatched)),
        "unmatched_distinct_keys": int(unmatched.nunique()),
        "unmatched_values": sorted(unmatched.unique().tolist()),
        "parent_keys_without_children": int((~parent_present.drop_duplicates().isin(child_present)).sum()),
        "parent_key_unique": bool(not repeated_parent),
        "maximum_child_rows_per_key": int(child_present.value_counts().max()),
    }


def quality_checks(tables):
    customers = tables["customers"]
    geolocation = tables["geolocation"]
    orders = tables["orders"]
    reviews = tables["order_reviews"]
    products = tables["products"]
    payments = tables["order_payments"]
    checks = {}

    customer_counts = customers.groupby("customer_unique_id").size()
    checks["customer_identity"] = {
        "customer_id_count": int(customers["customer_id"].nunique()),
        "customer_unique_id_count": int(customers["customer_unique_id"].nunique()),
        "unique_ids_with_multiple_customer_ids": int(customer_counts.gt(1).sum()),
        "maximum_customer_ids_per_unique_id": int(customer_counts.max()),
        "unique_ids_with_multiple_locations": int(customers.groupby("customer_unique_id")["customer_zip_code_prefix"].nunique().gt(1).sum()),
    }

    geo_groups = geolocation.groupby("geolocation_zip_code_prefix")
    latitudes = pd.to_numeric(geolocation["geolocation_lat"])
    longitudes = pd.to_numeric(geolocation["geolocation_lng"])
    # A broad screening rectangle, not an exact Brazil boundary or a deletion rule.
    outside_brazil_screen = ~latitudes.between(-35, 6) | ~longitudes.between(-75, -30)
    checks["geolocation"] = {
        "distinct_postal_prefixes": int(geo_groups.ngroups),
        "prefixes_with_multiple_cities": int(geo_groups["geolocation_city"].nunique().gt(1).sum()),
        "prefixes_with_multiple_states": int(geo_groups["geolocation_state"].nunique().gt(1).sum()),
        "globally_invalid_coordinate_rows": int((~latitudes.between(-90, 90) | ~longitudes.between(-180, 180)).sum()),
        "outside_broad_brazil_rectangle_rows": int(outside_brazil_screen.sum()),
        "brazil_screen_bounds": {"latitude": [-35, 6], "longitude": [-75, -30]},
    }

    dates = {}
    for column in orders.columns:
        if column in DATE_COLUMNS:
            dates[column] = pd.to_datetime(orders[column], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    timestamp_pairs = [
        ("approval_before_purchase", "order_approved_at", "order_purchase_timestamp"),
        ("carrier_before_purchase", "order_delivered_carrier_date", "order_purchase_timestamp"),
        ("delivery_before_purchase", "order_delivered_customer_date", "order_purchase_timestamp"),
        ("carrier_before_approval", "order_delivered_carrier_date", "order_approved_at"),
        ("delivery_before_carrier", "order_delivered_customer_date", "order_delivered_carrier_date"),
    ]
    checks["order_timestamps"] = {}
    for label, later_column, earlier_column in timestamp_pairs:
        both_present = dates[later_column].notna() & dates[earlier_column].notna()
        checks["order_timestamps"][label] = {
            "comparable_rows": int(both_present.sum()),
            "violating_rows": int((both_present & dates[later_column].lt(dates[earlier_column])).sum()),
        }
    checks["missing_order_dates_by_status"] = {}
    for status, group in orders.groupby("order_status"):
        checks["missing_order_dates_by_status"][status] = {
            "rows": int(len(group)),
            "missing": {column: int(missing_mask(group[column]).sum()) for column in dates},
        }

    creation = pd.to_datetime(reviews["review_creation_date"], format="%Y-%m-%d %H:%M:%S")
    answer = pd.to_datetime(reviews["review_answer_timestamp"], format="%Y-%m-%d %H:%M:%S")
    purchase_by_order = dates["order_purchase_timestamp"].set_axis(orders["order_id"])
    review_purchase = reviews["order_id"].map(purchase_by_order)
    checks["reviews"] = {
        "review_ids_linked_to_multiple_orders": int(reviews.groupby("review_id")["order_id"].nunique().gt(1).sum()),
        "reused_review_ids_with_conflicting_scores": int(reviews.groupby("review_id")["review_score"].nunique().gt(1).sum()),
        "orders_with_multiple_review_rows": int(reviews.groupby("order_id").size().gt(1).sum()),
        "answer_before_creation": int(answer.lt(creation).sum()),
        "creation_before_order_purchase": int(creation.lt(review_purchase).sum()),
        "creation_on_earlier_calendar_date_than_purchase": int(creation.dt.normalize().lt(review_purchase.dt.normalize()).sum()),
        "creation_before_purchase_but_same_calendar_date": int((creation.lt(review_purchase) & creation.dt.normalize().eq(review_purchase.dt.normalize())).sum()),
        "nonmidnight_creation_timestamps": int(creation.ne(creation.dt.normalize()).sum()),
        "scores_outside_1_to_5": int((~pd.to_numeric(reviews["review_score"]).between(1, 5)).sum()),
    }
    product_numbers = products[["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]].apply(pd.to_numeric, errors="coerce")
    checks["products"] = {
        "rows_with_missing_category": int(missing_mask(products["product_category_name"]).sum()),
        "rows_with_zero_weight": int(product_numbers["product_weight_g"].eq(0).sum()),
        "rows_with_nonpositive_dimensions": int(product_numbers[["product_length_cm", "product_height_cm", "product_width_cm"]].le(0).any(axis=1).sum()),
    }
    installment_numbers = pd.to_numeric(payments["payment_installments"])
    payment_numbers = pd.to_numeric(payments["payment_value"])
    checks["payments"] = {
        "zero_installment_rows": int(installment_numbers.eq(0).sum()),
        "zero_payment_value_rows": int(payment_numbers.eq(0).sum()),
        "zero_installment_payment_types": payments.loc[installment_numbers.eq(0), "payment_type"].value_counts().to_dict(),
        "zero_value_payment_types": payments.loc[payment_numbers.eq(0), "payment_type"].value_counts().to_dict(),
        "payment_type_counts": payments["payment_type"].value_counts().to_dict(),
    }
    items = tables["order_items"]
    shipping_limits = pd.to_datetime(items["shipping_limit_date"], format="%Y-%m-%d %H:%M:%S")
    checks["order_items"] = {
        "orders_without_items_by_status": orders.loc[~orders["order_id"].isin(items["order_id"]), "order_status"].value_counts().to_dict(),
        "shipping_limit_after_2018_rows": int(shipping_limits.ge("2019-01-01").sum()),
        "shipping_limit_before_purchase_rows": int(shipping_limits.lt(items["order_id"].map(purchase_by_order)).sum()),
    }
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Regenerate data/processed/data_profile.json; raw files remain read-only.")
    arguments = parser.parse_args()
    if OUTPUT_PATH.exists() and not arguments.overwrite:
        raise FileExistsError(f"Output already exists: {OUTPUT_PATH}. Use --overwrite to regenerate it.")
    actual_files = {path.name for path in RAW_DIRECTORY.glob("*.csv")}
    if actual_files != set(FILES.values()):
        raise ValueError("CSV inventory differs from the nine expected Olist files; review FILES before rerunning.")

    tables = {}
    profile = {"python_version": platform.python_version(), "pandas_version": pd.__version__, "tables": {}}
    for table_name, filename in FILES.items():
        path = RAW_DIRECTORY / filename
        before_hash = file_hash(path)
        # CSVs have no native schema. Read every value as text to preserve leading zeros.
        # utf-8-sig also handles the translation file's byte-order mark in its header.
        frame = pd.read_csv(path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
        tables[table_name] = frame
        profile["tables"][table_name] = {
            "filename": filename,
            "sha256": before_hash,
            "rows": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "duplicate_excess_rows": int(frame.duplicated().sum()),
            "rows_in_exact_duplicate_groups": int(frame.duplicated(keep=False).sum()),
            "columns": {name: profile_column(frame[name], name) for name in frame.columns},
            "key_checks": [profile_key(frame, columns) for columns in KEYS[table_name]],
        }
        print(f"Profiled {filename}: {len(frame):,} rows, {len(frame.columns)} columns", flush=True)
    profile["relationships"] = [profile_relationship(tables, *relationship) for relationship in RELATIONSHIPS]
    profile["quality_checks"] = quality_checks(tables)

    # Verify source bytes are unchanged before publishing the profile.
    for table_name, filename in FILES.items():
        if file_hash(RAW_DIRECTORY / filename) != profile["tables"][table_name]["sha256"]:
            raise RuntimeError(f"Raw file changed during profiling: {filename}")
    profile["raw_hashes_unchanged"] = True
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH}. All raw file hashes are unchanged.")


if __name__ == "__main__":
    main()
