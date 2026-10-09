"""Independent customer/cohort calculations from base tables, with Python integers.

Expected customer rows and aggregate outputs do not use analytical SQL or its CTEs.
No customer/order identifiers are written to evidence or exported CSVs.
"""

from collections import Counter, defaultdict
from datetime import datetime

from .validate_metrics import record_check


def month_number(month):
    year, number = map(int, month.split("-"))
    return year * 12 + number - 1


def month_text(number):
    return f"{number // 12:04d}-{number % 12 + 1:02d}"


def base_model(connection):
    customers = {r["customer_id"]: (r["customer_unique_id"], r["customer_state"]) for r in connection.execute("SELECT customer_id,customer_unique_id,customer_state FROM customers")}
    purchases, all_months = {}, Counter()
    groups = defaultdict(list)
    for row in connection.execute("SELECT order_id,customer_id,order_status,order_purchase_timestamp FROM orders"):
        all_months[row["order_purchase_timestamp"][:7]] += 1
        if row["order_status"] != "delivered":
            continue
        uid, state = customers[row["customer_id"]]
        timestamp = datetime.strptime(row["order_purchase_timestamp"], "%Y-%m-%d %H:%M:%S")
        order = {"order_id": row["order_id"], "uid": uid, "state": state, "timestamp": timestamp,
                 "sales": 0, "freight": 0, "items": 0, "categories": set()}
        purchases[row["order_id"]] = order
        groups[uid].append(order)
    products = dict(connection.execute("SELECT product_id,product_category_name FROM products"))
    translations = dict(connection.execute("SELECT product_category_name,product_category_name_english FROM product_categories"))
    order_categories = defaultdict(lambda: {"items": 0, "sales": 0})
    for row in connection.execute("SELECT order_id,product_id,price_hundredths,freight_value_hundredths FROM order_items"):
        if row["order_id"] not in purchases:
            continue
        if type(row["price_hundredths"]) is not int or type(row["freight_value_hundredths"]) is not int:
            raise ValueError("Noninteger source amounts")
        order = purchases[row["order_id"]]
        label = products[row["product_id"]]
        order["sales"] += row["price_hundredths"]
        order["freight"] += row["freight_value_hundredths"]
        order["items"] += 1
        order["categories"].add(label)
        category = order_categories[(row["order_id"], label)]
        category["items"] += 1
        category["sales"] += row["price_hundredths"]
    observation = max(order["timestamp"].date() for order in purchases.values())
    model = {}
    pairs = []
    for uid, rows in groups.items():
        rows.sort(key=lambda order: (order["timestamp"], order["order_id"]))
        first, last = rows[0]["timestamp"].date(), rows[-1]["timestamp"].date()
        states = {order["state"].strip() for order in rows if order["state"] and order["state"].strip()}
        missing_states = sum(not order["state"] or not order["state"].strip() for order in rows)
        sales = sum(order["sales"] for order in rows)
        state = next(iter(states)) if len(states) == 1 and not missing_states else None
        model[uid] = {
            "customer_unique_id": uid, "first_purchase_date": first.isoformat(), "last_purchase_date": last.isoformat(),
            "completed_order_count": len(rows), "item_sales_hundredths": sales,
            "freight_hundredths": sum(order["freight"] for order in rows), "items_purchased": sum(order["items"] for order in rows),
            "orders_missing_items": sum(order["items"] == 0 for order in rows), "distinct_customer_states": len(states),
            "orders_missing_state": missing_states, "customer_state": state,
            "average_order_value_hundredths_numerator": sales, "average_order_value_hundredths_denominator": len(rows),
            "average_order_value_hundredths": f"{sales}/{len(rows)}",
            "days_between_first_and_last_purchase": (last - first).days,
            "repeat_customer_flag": int(len(rows) >= 2), "observation_date": observation.isoformat(),
            "recency_days": (observation - last).days, "cohort_month": first.isoformat()[:7],
            "flag_customer_state_unassigned": int(state is None),
        }
        for index in range(1, len(rows)):
            old, new = rows[index - 1], rows[index]
            old_categories, new_categories = old["categories"], new["categories"]
            if not old_categories or not new_categories or None in old_categories or None in new_categories:
                behavior = "category_unknown"
            elif old_categories == new_categories:
                behavior = "same_category_set"
            elif old_categories & new_categories:
                behavior = "overlap_with_change"
            else:
                behavior = "no_category_overlap"
            pairs.append({"uid": uid, "first_to_second": index == 1,
                          "days": (new["timestamp"].date() - old["timestamp"].date()).days,
                          "tied": int(new["timestamp"] == old["timestamp"]), "behavior": behavior})
    values = sorted(row["item_sales_hundredths"] for row in model.values())
    recencies = sorted(row["recency_days"] for row in model.values())
    n = len(values)
    quantiles = {p: values[(n * p + 99) // 100 - 1] for p in (25, 50, 75, 90, 95, 99)}
    median_recency = recencies[(n + 1) // 2 - 1]
    fence_twice = 2 * quantiles[75] + 3 * (quantiles[75] - quantiles[25])
    for row in model.values():
        row["frequency_group"] = "Repeat" if row["repeat_customer_flag"] else "One-time"
        row["high_value_flag"] = int(2 * row["item_sales_hundredths"] > fence_twice)
        row["segment"] = ("High-value " if row["high_value_flag"] else "Standard ") + ("repeat" if row["repeat_customer_flag"] else "one-time")
        row["recency_group"] = "recent within observed period" if row["recency_days"] <= median_recency else "less recent within observed period"
    return model, groups, purchases, pairs, order_categories, translations, all_months, quantiles, median_recency, fence_twice


def group_metrics(rows, total_sales):
    sales, orders = sum(r["item_sales_hundredths"] for r in rows), sum(r["completed_order_count"] for r in rows)
    return {
        "customers": len(rows), "completed_orders": orders, "item_sales_hundredths": sales,
        "freight_hundredths": sum(r["freight_hundredths"] for r in rows),
        "average_customer_sales_hundredths_numerator": sales, "average_customer_sales_hundredths_denominator": len(rows),
        "average_order_value_hundredths_numerator": sales, "average_order_value_hundredths_denominator": orders,
        "sales_share_percent_numerator": 100 * sales, "sales_share_percent_denominator": total_sales,
    }


def cohort_expected(model, groups, all_months):
    cohorts = defaultdict(list)
    activities = defaultdict(set)
    same_month_repeat = Counter()
    first_month = min(r["cohort_month"] for r in model.values())
    last_month = max(r["last_purchase_date"][:7] for r in model.values())
    for uid, row in model.items():
        cohort = row["cohort_month"]
        cohorts[cohort].append(row)
        frequencies = Counter(order["timestamp"].strftime("%Y-%m") for order in groups[uid])
        same_month_repeat[cohort] += frequencies[cohort] >= 2
        for month in frequencies:
            activities[(cohort, month)].add(uid)
    horizon = max(3, month_number(last_month) - month_number(first_month))
    matrix, summaries = [], []
    for cohort in sorted(cohorts):
        rows = cohorts[cohort]
        n = len(rows)
        cells = []
        later = set()
        for index in range(horizon + 1):
            target = month_text(month_number(cohort) + index)
            status = "baseline_membership" if index == 0 else "future_unobserved" if target > last_month else "terminal_partial" if target == last_month else "calendar_gap" if not all_months[target] else "interior_observed"
            observed = len(activities[(cohort, target)]) if target <= last_month else None
            eligible = status in ("baseline_membership", "interior_observed")
            cells.append({"cohort_month": cohort, "new_customers": n, "month_index": index, "target_month": target,
                          "coverage_status": status, "observed_customers": observed,
                          "returning_customers_for_rate": observed if eligible else None,
                          "retention_percent_numerator": 100 * observed if eligible else None,
                          "retention_percent_denominator": n,
                          "flag_future_unobserved": int(status == "future_unobserved"),
                          "flag_terminal_partial": int(status == "terminal_partial"), "flag_calendar_gap": int(status == "calendar_gap")})
            if index >= 4 and status == "interior_observed":
                later.update(activities[(cohort, target)])
        sales = sum(r["item_sales_hundredths"] for r in rows)
        repeat = sum(r["repeat_customer_flag"] for r in rows)
        summary = {"cohort_month": cohort, "new_customers": n, "completed_orders": sum(r["completed_order_count"] for r in rows),
                   "repeat_customers": repeat, "item_sales_hundredths": sales, "freight_hundredths": sum(r["freight_hundredths"] for r in rows),
                   "items_purchased": sum(r["items_purchased"] for r in rows),
                   "average_customer_sales_hundredths_numerator": sales, "average_customer_sales_hundredths_denominator": n,
                   "observed_repeat_rate_percent_numerator": 100 * repeat, "observed_repeat_rate_percent_denominator": n,
                   "same_month_repeat_customers": same_month_repeat[cohort]}
        for index in (1, 2, 3):
            cell = cells[index]
            summary[f"customers_returning_month_{index}"] = cell["returning_customers_for_rate"]
            summary[f"month_{index}_coverage"] = cell["coverage_status"]
            summary[f"month_{index}_retention_percent_numerator"] = cell["retention_percent_numerator"]
            summary[f"month_{index}_retention_percent_denominator"] = n
        summary["customers_returning_month_4_plus"] = len(later) if any(c["month_index"] >= 4 and c["coverage_status"] == "interior_observed" for c in cells) else None
        summary["available_interior_future_months"] = sum(c["month_index"] > 0 and c["coverage_status"] == "interior_observed" for c in cells)
        summary["flag_insufficient_three_month_coverage"] = int(sum(cells[index]["coverage_status"] == "interior_observed" for index in (1, 2, 3)) < 3)
        summary["flag_initial_boundary_cohort"] = int(cohort == first_month)
        summary["flag_terminal_boundary_cohort"] = int(cohort == last_month)
        summaries.append(summary)
        matrix.extend(cells)
    return summaries, matrix


def validate_customer_analysis(connection, results, prefix, prior):
    findings = {"checks": []}
    model, groups, purchases, pairs, order_categories, translations, all_months, quantiles, recency_median, fence = base_model(connection)
    count = len(model)
    sales = sum(r["item_sales_hundredths"] for r in model.values())
    orders = sum(r["completed_order_count"] for r in model.values())
    repeat_count = sum(r["repeat_customer_flag"] for r in model.values())
    seen, errors = set(), 0
    for actual in connection.execute(prefix + "\nSELECT * FROM customer_level"):
        observed = dict(actual)
        uid = observed["customer_unique_id"]
        expected = {key: value for key, value in model[uid].items()
                    if key not in ("frequency_group", "high_value_flag", "segment", "recency_group")}
        errors += int(observed != expected or any(type(observed[key]) is not type(value) for key, value in expected.items()) or uid in seen)
        seen.add(uid)
    record_check(findings, "Customer-level rows: one per persistent ID; every date/state/value/recency field", [count, 0], [len(seen), errors])
    classification_errors = 0
    for actual in connection.execute(prefix + "\nSELECT customer_unique_id,frequency_group,high_value_flag,segment,recency_group FROM customer_segments"):
        row = dict(actual)
        classification_errors += int(any(row[key] != model[row["customer_unique_id"]][key] for key in row))
    record_check(findings, "Every customer's frequency/value/neutral-recency assignment", 0, classification_errors)
    for name, current, old in (("customers", count, prior["unique_customers"]), ("repeat customers", repeat_count, prior["customers_two_plus_completed_orders"]), ("completed orders", orders, prior["completed_orders"]), ("eligible item sales hundredths", sales, prior["item_sales_hundredths"])):
        record_check(findings, f"Prior independently validated {name}", old, current)
    frequency = []
    for number in sorted({r["completed_order_count"] for r in model.values()}):
        rows = [r for r in model.values() if r["completed_order_count"] == number]
        frequency.append({"completed_order_count": number, "customers": len(rows), "item_sales_hundredths": sum(r["item_sales_hundredths"] for r in rows), "freight_hundredths": sum(r["freight_hundredths"] for r in rows), "customer_share_percent_numerator": 100 * len(rows), "customer_share_percent_denominator": count})
    record_check(findings, "Full frequency distribution", frequency, results["frequency_distribution"])
    bins = defaultdict(list)
    for row in model.values():
        value = row["item_sales_hundredths"]
        label = "01_at_or_below_Q1" if value <= quantiles[25] else "02_Q1_to_median" if value <= quantiles[50] else "03_median_to_Q3" if value <= quantiles[75] else "04_above_Q3"
        bins[label].append(value)
    expected_bins = [{"value_bin": label, "customers": len(values), "min_sales_hundredths": min(values), "max_sales_hundredths": max(values), "item_sales_hundredths": sum(values)} for label, values in sorted(bins.items())]
    record_check(findings, "Value distribution with unsplit quartile ties", expected_bins, results["value_distribution"])
    values = sorted(r["item_sales_hundredths"] for r in model.values())
    statistic_values = (("minimum", values[0], 1), ("Q1", quantiles[25], 1), ("median", quantiles[50], 1), ("Q3", quantiles[75], 1), ("P90", quantiles[90], 1), ("P95", quantiles[95], 1), ("P99", quantiles[99], 1), ("maximum", values[-1], 1), ("mean", sales, count), ("Tukey_upper_fence", fence, 2), ("recency_median", recency_median, 1))
    statistics = [{"statistic": name, "unit": "calendar_days" if name == "recency_median" else "hundredths", "value_numerator": value, "value_denominator": denominator} for name, value, denominator in statistic_values]
    record_check(findings, "Quantiles, exact mean/fence and median recency", statistics, results["value_statistics"])
    group_rows, segment_rows, recency_rows = [], [], []
    for label in sorted({r["frequency_group"] for r in model.values()}):
        rows = [r for r in model.values() if r["frequency_group"] == label]
        group_rows.append({"frequency_group": label, **group_metrics(rows, sales)})
    record_check(findings, "One-time versus repeat customers: every mean and sales share", group_rows, results["purchase_group_comparison"])
    for label in sorted({r["segment"] for r in model.values()}):
        rows = [r for r in model.values() if r["segment"] == label]
        segment_rows.append({"segment": label, "frequency_group": rows[0]["frequency_group"], "high_value_flag": rows[0]["high_value_flag"], **group_metrics(rows, sales),
            "items_purchased": sum(r["items_purchased"] for r in rows), "customer_share_percent_numerator": 100 * len(rows), "customer_share_percent_denominator": count,
            "q1_hundredths": quantiles[25], "q3_hundredths": quantiles[75], "high_value_threshold_hundredths_numerator": fence, "high_value_threshold_hundredths_denominator": 2,
            "observation_date": rows[0]["observation_date"], "recency_median_days": recency_median,
            "recent_within_observed_period_customers": sum(r["recency_group"] == "recent within observed period" for r in rows), "customers_state_unassigned": sum(r["flag_customer_state_unassigned"] for r in rows)})
    record_check(findings, "Every segment count/value/frequency/recency/state field", segment_rows, results["customer_segments"])
    for label in sorted({r["recency_group"] for r in model.values()}):
        rows = [r for r in model.values() if r["recency_group"] == label]
        recency_rows.append({"recency_group": label, "observation_date": rows[0]["observation_date"], "recency_median_days": recency_median, "customers": len(rows), "min_recency_days": min(r["recency_days"] for r in rows), "max_recency_days": max(r["recency_days"] for r in rows), "item_sales_hundredths": sum(r["item_sales_hundredths"] for r in rows), "customers_state_unassigned": sum(r["flag_customer_state_unassigned"] for r in rows)})
    record_check(findings, "Neutral historical recency groups", recency_rows, results["recency_summary"])
    ranked = sorted(model.values(), key=lambda r: (-r["item_sales_hundredths"], r["customer_unique_id"]))
    cumulative, total = [], 0
    for row in ranked:
        total += row["item_sales_hundredths"]
        cumulative.append(total)
    pareto = []
    for percent in range(1, 101):
        k = (count * percent + 99) // 100
        pareto.append({"target_customer_percent": percent, "customers_selected": k, "total_customers": count, "actual_customer_percent_numerator": 100 * k, "actual_customer_percent_denominator": count,
                      "item_sales_hundredths": cumulative[k - 1], "cumulative_sales_percent_numerator": 100 * cumulative[k - 1], "cumulative_sales_percent_denominator": sales, "cutoff_customer_sales_hundredths": ranked[k - 1]["item_sales_hundredths"]})
    record_check(findings, "Every Pareto 1%-100% cutoff and cumulative sale", pareto, results["pareto_concentration"])
    k = next(index + 1 for index, amount in enumerate(cumulative) if 100 * amount >= 80 * sales)
    inverse = [{"target_sales_percent": 80, "customers_selected": k, "item_sales_hundredths": cumulative[k - 1], "customer_share_percent_numerator": 100 * k, "customer_share_percent_denominator": count, "sales_share_percent_numerator": 100 * cumulative[k - 1], "sales_share_percent_denominator": sales}]
    record_check(findings, "Actual customers required for 80% sales", inverse, results["customers_for_80_percent_sales"])
    cohorts, matrix = cohort_expected(model, groups, all_months)
    record_check(findings, "Every cohort count/value, fixed denominator and exposure flag", cohorts, results["customer_cohort_summary"])
    record_check(findings, "Every retention cell: customer/month uniqueness; future/gap/partial NULLs", matrix, results["cohort_retention_long"])
    first_pairs = [p for p in pairs if p["first_to_second"]]
    intervals = sorted(p["days"] for p in first_pairs)
    middle = [intervals[(len(intervals) - 1) // 2]] if len(intervals) % 2 else intervals[len(intervals) // 2 - 1:len(intervals) // 2 + 1]
    timing = [{"metric": "repeat_customers", "count": repeat_count, "value_numerator": None, "value_denominator": None},
              {"metric": "median_days_to_second_purchase", "count": repeat_count, "value_numerator": sum(middle), "value_denominator": len(middle)},
              {"metric": "same_day_second_purchase", "count": sum(p["days"] == 0 for p in first_pairs), "value_numerator": 100 * sum(p["days"] == 0 for p in first_pairs), "value_denominator": repeat_count},
              {"metric": "first_second_timestamp_ties", "count": sum(p["tied"] for p in first_pairs), "value_numerator": None, "value_denominator": None},
              {"metric": "all_consecutive_repeat_intervals", "count": len(pairs), "value_numerator": None, "value_denominator": None}]
    for days in (30, 60, 90, 180):
        n = sum(p["days"] <= days for p in first_pairs)
        timing.append({"metric": f"within_{days}_days", "count": n, "value_numerator": 100 * n, "value_denominator": repeat_count})
    record_check(findings, "First-to-second timing: exact median and conditional day-window shares", timing, results["repeat_purchase_summary"])
    interval_rows, transition_rows = [], []
    for scope, scoped in (("all_consecutive", pairs), ("first_to_second", first_pairs)):
        buckets = defaultdict(list)
        transitions = defaultdict(list)
        for pair in scoped:
            days = pair["days"]
            label = "01_same_day" if days == 0 else "02_1_to_30_days" if days <= 30 else "03_31_to_60_days" if days <= 60 else "04_61_to_90_days" if days <= 90 else "05_91_to_180_days" if days <= 180 else "06_181_to_365_days" if days <= 365 else "07_over_365_days"
            buckets[label].append(days)
            transitions[pair["behavior"]].append(pair)
        for label, days in sorted(buckets.items()):
            interval_rows.append({"scope": scope, "interval_bin": label, "intervals": len(days), "min_days": min(days), "max_days": max(days)})
        for label, rows in sorted(transitions.items()):
            transition_rows.append({"scope": scope, "behavior": label, "order_transitions": len(rows), "distinct_customers": len({p["uid"] for p in rows}), "tied_timestamp_transitions": sum(p["tied"] for p in rows), "transition_share_percent_numerator": 100 * len(rows), "transition_share_percent_denominator": len(scoped)})
    record_check(findings, "Both first-to-second and all-consecutive interval distributions", interval_rows, results["repeat_interval_distribution"])
    record_check(findings, "Category comparisons: one row per pair; NULLs unknown; every behavior share", transition_rows, results["category_transitions"])
    category_groups = defaultdict(lambda: {"uids": set(), "orders": set(), "items": 0, "sales": 0})
    for (order_id, category), detail in order_categories.items():
        uid = purchases[order_id]["uid"]
        group = category_groups[(model[uid]["frequency_group"], category)]
        group["uids"].add(uid)
        group["orders"].add(order_id)
        group["items"] += detail["items"]
        group["sales"] += detail["sales"]
    category_rows = []
    for frequency in ("One-time", "Repeat"):
        keys = sorted((key for key in category_groups if key[0] == frequency), key=lambda key: (-category_groups[key]["sales"], key[1] is not None, key[1] or ""))
        group_sales = sum(category_groups[key]["sales"] for key in keys)
        for rank, key in enumerate(keys, 1):
            detail = category_groups[key]
            category_rows.append({"frequency_group": frequency, "product_category_name": key[1], "product_category_name_english": translations.get(key[1]), "customers": len(detail["uids"]), "completed_orders": len(detail["orders"]), "items_purchased": detail["items"], "item_sales_hundredths": detail["sales"], "sales_rank": rank,
                                  "group_sales_share_percent_numerator": 100 * detail["sales"], "group_sales_share_percent_denominator": group_sales})
    record_check(findings, "Order/category aggregation: every one-time/repeat category count/sale/rank", category_rows, results["category_customer_behavior"])
    for label, rows in (("segments", results["customer_segments"]), ("cohorts", results["customer_cohort_summary"])):
        customer_field = "customers" if label == "segments" else "new_customers"
        record_check(findings, f"{label}: customers additive", count, sum(r[customer_field] for r in rows))
        record_check(findings, f"{label}: orders additive", orders, sum(r["completed_orders"] for r in rows))
        record_check(findings, f"{label}: INTEGER item sales additive", sales, sum(r["item_sales_hundredths"] for r in rows))
    record_check(findings, "All consecutive repeat joins have exactly orders minus customers rows", orders - count, len(pairs))
    record_check(findings, "Category group item sales reconcile to eligible total", sales, sum(r["item_sales_hundredths"] for r in category_rows))
    findings["summary"] = {"customers": count, "orders": orders, "item_sales_hundredths": sales, "repeat_customers": repeat_count, "observation_date": next(iter(model.values()))["observation_date"], "customer_state_unassigned": sum(r["flag_customer_state_unassigned"] for r in model.values()), "same_month_repeat_customers": sum(r["same_month_repeat_customers"] for r in cohorts)}
    failed = [check for check in findings["checks"] if not check["passed"]]
    if failed:
        # Retention/value outputs are aggregate-only; identifiers are never in diagnostics.
        raise ValueError("Customer analysis validation failed: " + str([c["name"] for c in failed]))
    return findings
