"""Required invariants stop publication; interpretable anomalies become flags."""

from decimal import Decimal
import pandas as pd

from .schema import (
    DATES, EXPECTED_COLUMNS, FOREIGN_KEYS, IDENTIFIERS, INTEGERS, KEYS, MONEY,
    ORDER_STATUSES, PAYMENT_TYPES, REQUIRED,
)


def require(condition, description, checks):
    checks.append({"check": description, "passed": bool(condition)})
    if not condition:
        raise ValueError(f"Data-quality check failed: {description}")


def validate_table(name, frame, details):
    checks = []
    require(set(EXPECTED_COLUMNS[name]).issubset(frame.columns), f"{name}: expected columns", checks)
    require(not frame[REQUIRED[name]].isna().any().any(), f"{name}: required fields populated", checks)
    require(not frame[KEYS[name]].isna().any().any(), f"{name}: key fields populated", checks)
    require(not frame.duplicated(KEYS[name]).any(), f"{name}: unique key {KEYS[name]}", checks)
    for column in IDENTIFIERS[name]:
        valid = frame[column].str.fullmatch(r"[0-9a-f]{32}").fillna(False)
        require(valid.all(), f"{name}.{column}: valid identifiers", checks)
    for column in frame.columns:
        if column.endswith("_zip_code_prefix"):
            valid = frame[column].str.fullmatch(r"\d{5}").fillna(False)
            require(valid.all(), f"{name}.{column}: five-character postal prefixes", checks)
        elif column.endswith("_state"):
            valid = frame[column].str.fullmatch(r"[A-Z]{2}").fillna(False)
            require(valid.all(), f"{name}.{column}: two-letter state labels", checks)
    for column in DATES.get(name, []):
        require(pd.api.types.is_datetime64_any_dtype(frame[column]), f"{name}.{column}: parsed timestamp type", checks)
    for column in INTEGERS.get(name, []):
        require(str(frame[column].dtype) == "Int64", f"{name}.{column}: nullable integer type", checks)
        require(frame[column].dropna().ge(0).all(), f"{name}.{column}: nonnegative integers", checks)
    for column in MONEY.get(name, []):
        valid = frame[column].dropna().map(lambda value: isinstance(value, Decimal) and value.is_finite() and value >= 0)
        require(valid.all(), f"{name}.{column}: exact nonnegative decimals", checks)
    if name == "orders":
        require(frame["order_status"].isin(ORDER_STATUSES).all(), "orders: recognized statuses", checks)
        require(not frame["customer_id"].duplicated().any(), "orders: one order per customer_id", checks)
    elif name == "order_items":
        require(frame["order_item_id"].gt(0).all(), "order_items: positive item sequence", checks)
    elif name == "payments":
        require(frame["payment_sequential"].gt(0).all(), "payments: positive payment sequence", checks)
        require(frame["payment_type"].isin(PAYMENT_TYPES).all(), "payments: recognized types", checks)
    elif name == "reviews":
        require(frame["review_score"].between(1, 5).all(), "reviews: scores between 1 and 5", checks)
    elif name == "products":
        for column in ["product_length_cm", "product_height_cm", "product_width_cm"]:
            require(frame[column].dropna().gt(0).all(), f"products.{column}: positive populated dimensions", checks)

    # Flags and lineage do not participate in business-record duplicate comparison.
    data_columns = EXPECTED_COLUMNS[name]
    after_duplicates = int(frame.duplicated(data_columns).sum())
    require(after_duplicates == 0, f"{name}: no duplicate prepared data rows", checks)
    expected_rows = details["original_rows"] - details["duplicates_removed"]
    require(len(frame) == expected_rows, f"{name}: source-to-output row reconciliation", checks)
    require(frame["source_record_number"].is_unique, f"{name}: unique source record lineage", checks)
    return checks


def validate_relationships(tables):
    checks = []
    for child_name, child_column, parent_name, parent_column in FOREIGN_KEYS:
        valid = tables[child_name][child_column].isin(tables[parent_name][parent_column])
        require(valid.all(), f"{child_name}.{child_column} references {parent_name}.{parent_column}", checks)
    customer_ids = set(tables["customers"]["customer_id"])
    order_customer_ids = set(tables["orders"]["customer_id"])
    require(customer_ids == order_customer_ids, "customers and orders: complete one-to-one customer_id coverage", checks)
    # Deliberately do not require customer_unique_id to be unique across records.
    return checks


def add_relationship_flags(tables, geo_prefixes):
    orders = tables["orders"]
    items = tables["order_items"]
    reviews = tables["reviews"]
    products = tables["products"]
    purchase_by_order = orders.set_index("order_id")["order_purchase_timestamp"]
    item_purchase = items["order_id"].map(purchase_by_order)
    items["flag_shipping_limit_before_purchase"] = items["shipping_limit_date"].lt(item_purchase)
    last_purchase_year = int(orders["order_purchase_timestamp"].dt.year.max())
    items["flag_shipping_limit_beyond_purchase_year"] = items["shipping_limit_date"].dt.year.gt(last_purchase_year)
    review_purchase = reviews["order_id"].map(purchase_by_order)
    reviews["flag_creation_before_purchase"] = reviews["review_creation_date"].lt(review_purchase)
    reviews["flag_creation_on_earlier_purchase_date"] = reviews["review_creation_date"].dt.normalize().lt(review_purchase.dt.normalize())
    reviews["flag_creation_before_purchase_same_date"] = (
        reviews["flag_creation_before_purchase"]
        & reviews["review_creation_date"].dt.normalize().eq(review_purchase.dt.normalize())
    )
    products["flag_category_translation_missing"] = (
        products["product_category_name"].notna()
        & ~products["product_category_name"].isin(tables["category_translation"]["product_category_name"])
    )
    orders["flag_items_missing"] = ~orders["order_id"].isin(items["order_id"])
    orders["flag_payments_missing"] = ~orders["order_id"].isin(tables["payments"]["order_id"])
    orders["flag_reviews_missing"] = ~orders["order_id"].isin(reviews["order_id"])
    for name, prefix in [("customers", "customer_zip_code_prefix"), ("sellers", "seller_zip_code_prefix")]:
        tables[name]["flag_geolocation_missing"] = ~tables[name][prefix].isin(geo_prefixes)


def verify_csv_round_trip(path, frame):
    """Read the saved file as text and compare every serialized field."""
    saved = pd.read_csv(path, dtype="string", keep_default_na=False, encoding="utf-8")
    expected = frame.copy()
    for column in expected.columns:
        if pd.api.types.is_datetime64_any_dtype(expected[column]):
            expected[column] = expected[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    expected = expected.astype("string").fillna("")
    pd.testing.assert_frame_equal(saved, expected, check_dtype=False)
