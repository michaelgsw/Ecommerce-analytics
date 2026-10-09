"""Independent Python reconciliation using only INTEGER base-table fields.

This module does not derive expected metrics from the analytical SQL/CTEs.
It reads base records, aggregates independently, and compares every output field.
No Decimal display helpers or SQL business-query functions are imported.
"""

from collections import Counter, defaultdict

ITEM_FIELDS = ("item_count", "item_sales_hundredths", "freight_hundredths", "items_shipping_before_purchase", "items_unusual_shipping_year")
PAYMENT_FIELDS = ("payment_record_count", "payment_total_hundredths", "payments_zero_installments", "payments_zero_value", "payments_undefined_type")
REVIEW_FIELDS = ("review_count", "review_score_total", "reviews_missing_title", "reviews_missing_message", "reviews_answer_before_creation", "reviews_creation_before_purchase", "reviews_earlier_purchase_date", "reviews_same_day_before_purchase")
CHILD_FLAGS = (*ITEM_FIELDS[3:], *PAYMENT_FIELDS[2:], *REVIEW_FIELDS[2:])


def record_check(findings, name, expected, observed):
    def same(left, right):
        if isinstance(left, dict) and isinstance(right, dict):
            return left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
        if isinstance(left, list) and isinstance(right, list):
            return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
        return type(left) is type(right) and left == right
    passed = same(expected, observed)
    findings["checks"].append({"name": name, "passed": passed, "expected": expected, "observed": observed})


def read_base_tables(connection):
    orders = {row["order_id"]: dict(row) for row in connection.execute("SELECT * FROM orders")}
    customers = {row["customer_id"]: dict(row) for row in connection.execute("SELECT customer_id, customer_unique_id, flag_geolocation_missing FROM customers")}
    products = {row["product_id"]: row["product_category_name"] for row in connection.execute("SELECT product_id, product_category_name FROM products")}
    categories = {row["product_category_name"]: row["product_category_name_english"] for row in connection.execute("SELECT product_category_name, product_category_name_english FROM product_categories")}
    items = defaultdict(lambda: dict.fromkeys(ITEM_FIELDS, 0))
    payments = defaultdict(lambda: dict.fromkeys(PAYMENT_FIELDS, 0))
    reviews = defaultdict(lambda: dict.fromkeys(REVIEW_FIELDS, 0))
    category_details = defaultdict(lambda: {"orders": set(), "products": set(), "items_sold": 0, "item_sales_hundredths": 0, "freight_hundredths": 0})
    for row in connection.execute("SELECT order_id, product_id, price_hundredths, freight_value_hundredths, flag_shipping_limit_before_purchase, flag_shipping_limit_beyond_purchase_year FROM order_items"):
        if type(row["price_hundredths"]) is not int or type(row["freight_value_hundredths"]) is not int:
            raise ValueError("Source item monetary storage is not INTEGER")
        entry = items[row["order_id"]]
        for key, value in zip(ITEM_FIELDS, (1, row["price_hundredths"], row["freight_value_hundredths"], row["flag_shipping_limit_before_purchase"], row["flag_shipping_limit_beyond_purchase_year"])):
            entry[key] += value
        if orders[row["order_id"]]["order_status"] == "delivered":
            entry = category_details[products[row["product_id"]]]
            entry["orders"].add(row["order_id"])
            entry["products"].add(row["product_id"])
            entry["items_sold"] += 1
            entry["item_sales_hundredths"] += row["price_hundredths"]
            entry["freight_hundredths"] += row["freight_value_hundredths"]
    for row in connection.execute("SELECT order_id, payment_value_hundredths, flag_installments_zero, flag_payment_value_zero, flag_payment_type_undefined FROM payments"):
        if type(row["payment_value_hundredths"]) is not int:
            raise ValueError("Source payment monetary storage is not INTEGER")
        entry = payments[row["order_id"]]
        for key, value in zip(PAYMENT_FIELDS, (1, row["payment_value_hundredths"], row["flag_installments_zero"], row["flag_payment_value_zero"], row["flag_payment_type_undefined"])):
            entry[key] += value
    for row in connection.execute("SELECT order_id, review_score, flag_title_missing, flag_message_missing, flag_answer_before_creation, flag_creation_before_purchase, flag_creation_on_earlier_purchase_date, flag_creation_before_purchase_same_date FROM reviews"):
        entry = reviews[row["order_id"]]
        values = (1, row["review_score"], row["flag_title_missing"], row["flag_message_missing"], row["flag_answer_before_creation"], row["flag_creation_before_purchase"], row["flag_creation_on_earlier_purchase_date"], row["flag_creation_before_purchase_same_date"])
        for key, value in zip(REVIEW_FIELDS, values):
            entry[key] += value
    return orders, customers, categories, items, payments, reviews, category_details


def expected_order(order, customers, items, payments, reviews):
    order_id = order["order_id"]
    customer = customers[order["customer_id"]]
    expected = dict(order)
    expected["customer_unique_id"] = customer["customer_unique_id"]
    expected["customer_flag_geolocation_missing"] = customer["flag_geolocation_missing"]
    for records, fields in ((items, ITEM_FIELDS), (payments, PAYMENT_FIELDS), (reviews, REVIEW_FIELDS)):
        entry = records.get(order_id)
        for key in fields:
            # Unknown money/score sums are NULL when no source child exists.
            expected[key] = entry[key] if entry is not None else (None if key.endswith("_hundredths") or key == "review_score_total" else 0)
    entry = reviews.get(order_id)
    expected["average_review_score"] = f"{entry['review_score_total']}/{entry['review_count']}" if entry else None
    return expected


def summary(order_ids, orders, customers, items, payments, reviews):
    identities = {customers[orders[key]["customer_id"]]["customer_unique_id"] for key in order_ids}
    sales = sum(items[key]["item_sales_hundredths"] for key in order_ids if key in items)
    freight = sum(items[key]["freight_hundredths"] for key in order_ids if key in items)
    item_count = sum(items[key]["item_count"] for key in order_ids if key in items)
    purchases = [orders[key]["order_purchase_timestamp"] for key in order_ids]
    return {
        "completed_orders": len(order_ids), "distinct_customers": len(identities),
        "item_sales_hundredths": sales, "freight_hundredths": freight, "items_sold": item_count,
        "average_order_value_hundredths_numerator": sales,
        "average_order_value_hundredths_denominator": len(order_ids),
        "average_items_per_order_numerator": item_count, "average_items_per_order_denominator": len(order_ids),
        "payment_total_hundredths": sum(payments[key]["payment_total_hundredths"] for key in order_ids if key in payments),
        "orders_missing_items": sum(key not in items for key in order_ids),
        "orders_missing_payments": sum(key not in payments for key in order_ids),
        "orders_missing_reviews": sum(key not in reviews for key in order_ids),
        "first_completed_purchase_timestamp": min(purchases) if purchases else None,
        "last_completed_purchase_timestamp": max(purchases) if purchases else None,
    }


def expected_months(orders, customers, items, payments, reviews):
    by_month = defaultdict(list)
    for key, order in orders.items():
        by_month[order["order_purchase_timestamp"][:7]].append(key)
    first, last = min(by_month), max(by_month)
    completed_months = sorted({order["order_purchase_timestamp"][:7] for order in orders.values() if order["order_status"] == "delivered"})
    completed_boundaries = {completed_months[0], completed_months[-1]} if completed_months else set()
    month, previous, rows = first, None, []
    while month <= last:
        keys = by_month[month]
        eligible = [key for key in keys if orders[key]["order_status"] == "delivered"]
        metrics = summary(eligible, orders, customers, items, payments, reviews)
        row = {"month": month, "all_orders": len(keys)}
        for name in ("completed_orders", "distinct_customers", "item_sales_hundredths", "freight_hundredths", "items_sold", "orders_missing_items", "average_order_value_hundredths_numerator", "average_order_value_hundredths_denominator"):
            row[name] = metrics[name]
        row["flag_extract_boundary_month"] = int(month in {first, last})
        row["flag_completed_sales_boundary_month"] = int(month in completed_boundaries)
        row["flag_no_observed_orders"] = int(not keys)
        warnings = ("flag_extract_boundary_month", "flag_completed_sales_boundary_month", "flag_no_observed_orders")
        comparable = previous is not None and not any(row[k] or previous[k] for k in warnings)
        row["flag_mom_comparable"] = int(comparable)
        for metric, previous_name, change_name, ratio in (
            ("completed_orders", "previous_completed_orders", "completed_orders_mom_change", "completed_orders_mom_percent"),
            ("item_sales_hundredths", "previous_item_sales_hundredths", "item_sales_mom_change_hundredths", "item_sales_mom_percent"),
        ):
            old = previous[metric] if previous else None
            row[previous_name] = old
            row[change_name] = row[metric] - old if old is not None else None
            row[f"{ratio}_numerator"] = 100 * row[change_name] if comparable and old > 0 else None
            row[f"{ratio}_denominator"] = old if comparable and old > 0 else None
        rows.append(row)
        previous = row
        year, number = map(int, month.split("-"))
        month = f"{year + (number == 12):04d}-{1 if number == 12 else number + 1:02d}"
    return rows


def payment_reconciliation(keys, items, payments):
    groups = {name: {"orders": 0, "item_plus_freight_hundredths": 0, "payment_hundredths": 0, "difference_hundredths": 0} for name in ("both_present", "items_only", "payments_only", "neither_present")}
    differences = Counter()
    for key in keys:
        group = "both_present" if key in items and key in payments else "items_only" if key in items else "payments_only" if key in payments else "neither_present"
        gross = items[key]["item_sales_hundredths"] + items[key]["freight_hundredths"] if key in items else 0
        paid = payments[key]["payment_total_hundredths"] if key in payments else 0
        detail = groups[group]
        detail["orders"] += 1
        detail["item_plus_freight_hundredths"] += gross
        detail["payment_hundredths"] += paid
        detail["difference_hundredths"] += paid - gross
        if group == "both_present":
            differences[paid - gross] += 1
    return {
        "orders": len(keys), "item_plus_freight_hundredths": sum(g["item_plus_freight_hundredths"] for g in groups.values()),
        "payment_hundredths": sum(g["payment_hundredths"] for g in groups.values()),
        "difference_hundredths": sum(g["difference_hundredths"] for g in groups.values()),
        "coverage_groups": groups,
        "matched_orders": differences[0], "positive_difference_orders": sum(n for delta, n in differences.items() if delta > 0),
        "negative_difference_orders": sum(n for delta, n in differences.items() if delta < 0),
        "absolute_difference_one_or_two_hundredths_orders": sum(n for delta, n in differences.items() if abs(delta) in (1, 2)),
        "most_common_comparable_differences": [{"difference_hundredths": delta, "orders": count} for delta, count in differences.most_common(10)],
    }


def validate_metrics(connection, results, shared):
    findings = {"checks": [], "reconciliation": {}}
    orders, customers, categories, items, payments, reviews, category_details = read_base_tables(connection)
    delivered = [key for key, order in orders.items() if order["order_status"] == "delivered"]
    source_flags = [key for key in next(iter(orders.values())) if key.startswith("flag_")]
    seen, mismatches = set(), 0
    for actual in connection.execute(shared + "\nSELECT * FROM order_level"):
        row = dict(actual)
        key = row["order_id"]
        expected = expected_order(orders[key], customers, items, payments, reviews)
        mismatches += int(row != expected or any(type(row[k]) is not type(v) for k, v in expected.items()))
        if key in seen:
            mismatches += 1
        seen.add(key)
    record_check(findings, "One order-level row per source order; every aggregate/identity/flag correct", [len(orders), 0], [len(seen), mismatches])
    for name, expected in (("order_item_summary", items), ("payment_summary", payments), ("review_summary", reviews)):
        actual = {row["order_id"]: {k: v for k, v in dict(row).items() if k != "order_id"} for row in connection.execute(shared + f"\nSELECT * FROM {name}")}
        if name == "review_summary":
            expected = {key: {**entry, "average_review_score": f"{entry['review_score_total']}/{entry['review_count']}"} for key, entry in expected.items()}
        record_check(findings, f"Every {name} group reconciles to independent base records", True, actual == expected)
    overview = summary(delivered, orders, customers, items, payments, reviews)
    record_check(findings, "Sales overview: every KPI independently recomputed", [overview], results["sales_overview"])
    monthly = expected_months(orders, customers, items, payments, reviews)
    record_check(findings, "Monthly: complete calendar, every KPI/lag/boundary rule", monthly, results["monthly_sales"])
    category_rows = []
    ordered_categories = sorted(category_details, key=lambda key: (-category_details[key]["item_sales_hundredths"], key is not None, key or ""))
    for rank, key in enumerate(ordered_categories, 1):
        entry = category_details[key]
        sales = entry["item_sales_hundredths"]
        category_rows.append({
            "product_category_name": key, "product_category_name_english": categories.get(key),
            "flag_category_missing": int(key is None), "flag_translation_missing": int(key is not None and categories.get(key) is None),
            "completed_orders": len(entry["orders"]), "products_sold": len(entry["products"]),
            "items_sold": entry["items_sold"], "item_sales_hundredths": sales, "freight_hundredths": entry["freight_hundredths"],
            "average_item_price_hundredths_numerator": sales, "average_item_price_hundredths_denominator": entry["items_sold"],
            "sales_share_percent_numerator": 100 * sales, "sales_share_percent_denominator": overview["item_sales_hundredths"],
            "sales_rank": rank, "is_top_10": int(rank <= 10),
        })
    record_check(findings, "Category: every KPI/rank, NULL and untranslated labels preserved", category_rows, results["category_performance"])
    customer_orders = Counter(customers[orders[key]["customer_id"]]["customer_unique_id"] for key in delivered)
    repeat = sum(count >= 2 for count in customer_orders.values())
    unique = len(customer_orders)
    customer_overview = {
        "unique_customers": unique, "customers_one_completed_order": sum(count == 1 for count in customer_orders.values()),
        "customers_two_plus_completed_orders": repeat, "completed_orders": len(delivered), "item_sales_hundredths": overview["item_sales_hundredths"],
        "repeat_customer_rate_percent_numerator": 100 * repeat, "repeat_customer_rate_percent_denominator": unique,
        "average_completed_orders_per_customer_numerator": len(delivered), "average_completed_orders_per_customer_denominator": unique,
        "average_completed_sales_per_customer_hundredths_numerator": overview["item_sales_hundredths"], "average_completed_sales_per_customer_hundredths_denominator": unique,
        "orders_missing_items": overview["orders_missing_items"],
    }
    record_check(findings, "Customer overview: persistent-ID counts, repeat rate, and all rational components", [customer_overview], results["customer_overview"])
    statuses = Counter(order["order_status"] for order in orders.values())
    operational = []
    for status in sorted(statuses, key=lambda label: (-statuses[label], label)):
        keys = [key for key, order in orders.items() if order["order_status"] == status]
        row = {"order_status": status, "orders": len(keys), "status_share_percent_numerator": 100 * len(keys), "status_share_percent_denominator": len(orders)}
        for metric, label in (("cancellation_rate_percent", "canceled"), ("unavailable_order_rate_percent", "unavailable"), ("delivered_order_rate_percent", "delivered")):
            row[f"{metric}_numerator"], row[f"{metric}_denominator"] = 100 * statuses[label], len(orders)
        row.update({"orders_missing_items": sum(key not in items for key in keys), "orders_missing_payments": sum(key not in payments for key in keys), "orders_missing_reviews": sum(key not in reviews for key in keys)})
        for flag in source_flags:
            row[flag] = sum(orders[key][flag] for key in keys)
        row["customer_flag_geolocation_missing"] = sum(customers[orders[key]["customer_id"]]["flag_geolocation_missing"] for key in keys)
        for flag in CHILD_FLAGS:
            source = items if flag in ITEM_FIELDS else payments if flag in PAYMENT_FIELDS else reviews
            row[flag] = sum(source[key][flag] for key in keys if key in source)
        operational.append(row)
    record_check(findings, "Operations: every status, rate, missing-child count, and source flag", operational, results["order_status_summary"])
    for row in results["sql_validation"]:
        record_check(findings, f"Saved SQL reconciliation: {row['check_name']}", row["expected_integer"], row["observed_integer"])
    for field in ("completed_orders", "item_sales_hundredths", "freight_hundredths", "items_sold"):
        record_check(findings, f"Monthly totals reconcile: {field}", overview[field], sum(row[field] for row in results["monthly_sales"]))
    for field in ("item_sales_hundredths", "freight_hundredths", "items_sold"):
        record_check(findings, f"Category totals reconcile: {field}", overview[field], sum(row[field] for row in results["category_performance"]))
    # Independently accumulate sales by identity without the SQL customer aggregation.
    customer_sales = Counter()
    for key in delivered:
        customer_sales[customers[orders[key]["customer_id"]]["customer_unique_id"]] += items[key]["item_sales_hundredths"] if key in items else 0
    record_check(findings, "Customer-level item sales are additive to eligible sales", overview["item_sales_hundredths"], sum(customer_sales.values()))
    record_check(findings, "Completed-order counts agree in sales/customer/operations", [len(delivered)] * 3, [results["sales_overview"][0]["completed_orders"], results["customer_overview"][0]["completed_orders"], next(row["orders"] for row in operational if row["order_status"] == "delivered")])
    record_check(findings, "Category-order coverage equals eligible orders with items", len(delivered) - overview["orders_missing_items"], len(set().union(*(entry["orders"] for entry in category_details.values()))))
    findings["reconciliation"]["all_orders"] = payment_reconciliation(list(orders), items, payments)
    findings["reconciliation"]["delivered_orders"] = payment_reconciliation(delivered, items, payments)
    for scope, detail in findings["reconciliation"].items():
        record_check(findings, f"Payment difference decomposition ({scope}); equality NOT required", detail["payment_hundredths"] - detail["item_plus_freight_hundredths"], detail["difference_hundredths"])
    findings["anomalies"] = {
        "order_flags_all_orders": {flag: sum(order[flag] for order in orders.values()) for flag in source_flags},
        "order_flags_delivered": {flag: sum(orders[key][flag] for key in delivered) for flag in source_flags},
        "delivered_orders_with_any_lifecycle_flag": sum(any(orders[key][flag] for flag in source_flags if flag not in ("flag_items_missing", "flag_payments_missing", "flag_reviews_missing")) for key in delivered),
        "delivered_review_creation_before_purchase_records": sum(reviews[key]["reviews_creation_before_purchase"] for key in delivered if key in reviews),
    }
    failed = [check for check in findings["checks"] if not check["passed"]]
    if failed:
        raise ValueError(f"Business metric reconciliation failed: {failed}")
    return findings
