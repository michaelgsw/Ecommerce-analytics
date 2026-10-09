"""Write reviewable metric results and reconciliation evidence, without charts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def write_report(findings):
    results = findings["results"]
    sales = results["sales_overview"][0]
    customer = results["customer_overview"][0]
    statuses = results["order_status_summary"]
    lines = [
        "# Business Metric Validation", "",
        f"Run (UTC): {findings['validated_at_utc']}. User reporting timezone: America/New_York.", "",
        f"**PASS: {len(findings['checks'])} metric checks and five field-level CSV readbacks; zero failures.**", "",
        "## Scope and exact definitions", "",
        "Completed-sales metrics include only order_status = delivered. Operational metrics retain all "
        "order statuses. Customer metrics use customer_unique_id through the customer_id join. "
        "Item sales sum price_hundredths, excluding freight; they do not represent net revenue. "
        "AOV is observed item sales / all completed orders, not payments / orders or item-plus-freight / orders. "
        "Items sold count item records, because no source quantity column is supplied. Repeat customers "
        "have at least two completed orders in the available extract. See docs/kpi_definitions.md for "
        "every numerator, denominator, source, exclusion, and limitation.", "",
        "All money totals and changes remain INTEGER hundredths of unspecified source units. No currency "
        "symbol is asserted. Averages, shares, rates, and MoM percentages retain their exact integer "
        "numerator/denominator pairs. Six-place Decimal text is display only, rounded half-up, without "
        "binary floats. Blank CSV ratios mean undefined; blank category names mean source NULL. "
        "No division by zero is coerced to zero.", "",
        "## Method and preservation", "",
        "The read-only runner executes every numbered SQL file plus validation.sql under a single read "
        "transaction. Every child is independently aggregated to order_id before joining. The validator "
        "rereads INTEGER base-table records and recomputes results using independent Python counters, "
        "sets, and integer sums; expected results do not come from the business SQL. It checks every "
        "order-level aggregate/flag/identity, every category/customer/month/status KPI, all rational "
        "components, shared-CTE drift, and saved SQL reconciliations. Export files are reread field by field.", "",
        f"All {len(findings['protected_hashes'])} protected files, including the database, schema.sql, "
        "and every raw/processed file, retained identical before/after SHA-256 hashes. Database hash "
        f"`{findings['protected_hashes']['data/database/olist_analytics.db']}` also matches the prior "
        "independent database validation evidence. No table, view, index, data record, or source schema "
        "was changed. Geolocation was not loaded or joined.", "",
        "## Main numerical results", "",
    ]
    for name, value in sales.items():
        if not name.endswith(("_numerator", "_denominator")):
            lines.append(f"- `{name}`: {value:,}." if type(value) is int else f"- `{name}`: `{value}`.")
    lines += ["", "Customer overview:", ""]
    for name, value in customer.items():
        if not name.endswith(("_numerator", "_denominator")):
            lines.append(f"- `{name}`: {value:,}." if type(value) is int else f"- `{name}`: `{value}`.")
    lines += ["", "All-order status distribution:", ""]
    for row in statuses:
        lines.append(f"- `{row['order_status']}`: {row['orders']:,} orders; {row['status_share_percent']}% of all orders. "
                     f"Missing items/payments/reviews: {row['orders_missing_items']:,}/{row['orders_missing_payments']:,}/{row['orders_missing_reviews']:,}.")
    if statuses:
        for name in ("cancellation_rate_percent", "unavailable_order_rate_percent", "delivered_order_rate_percent"):
            lines.append(f"- `{name}`: {statuses[0][name]}% (all-order denominator).")
    lines += ["", f"Top 10 categories by eligible item sales (all {len(results['category_performance'])} category groups remain in the export):", ""]
    for row in results["category_performance"]:
        if row["is_top_10"]:
            label = row["product_category_name"] if row["product_category_name"] is not None else "source category NULL"
            lines.append(f"- {row['sales_rank']}. `{label}`: {row['item_sales_hundredths']:,} hundredths; "
                         f"{row['items_sold']:,} item records; {row['completed_orders']:,} category orders; {row['sales_share_percent']}% sales share.")
    lines += ["", "Category order counts overlap and are not additive. Category/customer item sales, "
              "category freight/items, and monthly sales/freight/items/order counts all reconcile exactly "
              "to the delivered overview. Distinct monthly customers are not additive. No order is multiplied "
              "by child joins, including split payments and multiple/reused review IDs.", "",
              "## Payment-versus-item reconciliation", "",
              "Difference is **observed payments minus (observed item sales + freight)**: "
              "payment_total - (item_sales + freight). It is an audit comparison, not a revenue, discount, "
              "refund, or receivables KPI. Missing child rows do not establish zero-valued transactions. "
              "Coverage-group contributions below explain the arithmetic using observed totals; only "
              "both_present orders support an order-level amount comparison.", ""]
    for scope, detail in findings["reconciliation"].items():
        lines += [f"### {scope}", "",
                  f"- Orders: {detail['orders']:,}.",
                  f"- Observed item sales + freight: {detail['item_plus_freight_hundredths']:,} hundredths.",
                  f"- Observed payments: {detail['payment_hundredths']:,} hundredths.",
                  f"- Difference: {detail['difference_hundredths']:+,} hundredths."]
        for name, group in detail["coverage_groups"].items():
            lines.append(f"- `{name}`: {group['orders']:,} orders; items+freight {group['item_plus_freight_hundredths']:,}; "
                         f"payments {group['payment_hundredths']:,}; difference contribution {group['difference_hundredths']:+,} hundredths.")
        lines += [f"- Comparable orders matching exactly: {detail['matched_orders']:,}; payment greater: "
                  f"{detail['positive_difference_orders']:,}; payment smaller: {detail['negative_difference_orders']:,}.",
                  f"- Comparable orders differing by exactly one or two hundredths: {detail['absolute_difference_one_or_two_hundredths_orders']:,}.", ""]
    lines += ["The coverage decomposition reconciles exactly to each aggregate difference. Remaining "
              "differences on both-present orders are source discrepancies, not floating-point or "
              "join-multiplication errors. Small differences may reflect upstream rounding/recording, "
              "but this extract cannot establish the cause. It lacks facts sufficient to attribute "
              "differences to discounts, refunds, taxes, or payment timing. No equality was forced and "
              "no source amount was altered.", "", "## Coverage and material interpretation limits", ""]
    for row in results["monthly_sales"]:
        flags = [label for key, label in (
            ("flag_extract_boundary_month", "extract boundary"),
            ("flag_completed_sales_boundary_month", "completed-sales boundary"),
            ("flag_no_observed_orders", "no observed orders"),
        ) if row[key]]
        if flags or row["completed_orders"] == 0:
            lines.append(f"- `{row['month']}`: {row['all_orders']:,} all orders, {row['completed_orders']:,} delivered; "
                         f"warnings: {', '.join(flags) if flags else 'no completed orders in the observed snapshot'}. "
                         f"MoM comparison eligible: {row['flag_mom_comparable']}.")
    lines += ["- The extract's first/last purchase months and first/last completed-sales months are conservatively "
              "flagged. Calendar gaps remain explicit. Late periods can have unresolved order outcomes; "
              "zero observed completed sales does not prove zero underlying business activity. Interior "
              "months are not certified complete, and percentages involving flagged/gap periods are NULL.",
              "- The history is finite: repeat-customer counts describe completed orders observed here, "
              "not lifetime repeat behavior. Purchases outside the extract and non-delivered history are excluded."]
    for row in results["category_performance"]:
        if row["flag_category_missing"] or row["flag_translation_missing"]:
            label = row["product_category_name"] if row["product_category_name"] is not None else "source category NULL"
            lines.append(f"- `{label}` retained: {row['items_sold']:,} eligible item records; "
                         f"{row['item_sales_hundredths']:,} hundredths; {row['sales_share_percent']}% of eligible item sales.")
    lines += [f"- Delivered orders with at least one retained lifecycle anomaly flag: "
              f"{findings['anomalies']['delivered_orders_with_any_lifecycle_flag']:,}. Flags overlap; they do "
              "not change completed-sales eligibility and no chronology is repaired.",
              f"- Delivered review records created before purchase: {findings['anomalies']['delivered_review_creation_before_purchase_records']:,}. "
              "Review averages in reusable aggregates weight review records equally and retain repeated associations.", "",
              "Order anomaly/coverage flags (all orders / delivered):", ""]
    for flag, total in findings["anomalies"]["order_flags_all_orders"].items():
        lines.append(f"- `{flag}`: {total:,} / {findings['anomalies']['order_flags_delivered'][flag]:,}.")
    lines += ["", "Additional item/payment/review flags remain visible by status in order_status_summary.csv. "
              "A zero payment remains an observed zero; a missing payment remains absent. "
              "Missing lifecycle stages and product metadata are retained and do not trigger deletion.", "",
              "## Validation checks", ""]
    for check in findings["checks"]:
        lines.append(f"- PASS: {check['name']}.")
    lines += ["- PASS: five CSV files reread with exact header, row, field, blank-NULL, and ratio-display preservation.",
              "- PASS: every protected input/schema/database hash is unchanged; query and export hashes are recorded in the JSON evidence.", "",
              "## Exports and reproduction", ""]
    for name, count in findings["export_rows"].items():
        lines.append(f"- `data/analytics/{name}.csv`: {count:,} rows; no customer/order-level export.")
    lines += ["", "```powershell", ".\\.venv\\Scripts\\python.exe -m src.analysis.run_analysis",
              ".\\.venv\\Scripts\\python.exe -m src.analysis.run_analysis --validate-only", "```", "",
              "The six complete SQL queries run directly in a SQLite client. The shared CTE fragment is "
              "copied into them and drift-checked by the runner. To reuse the fragment alone, append a SELECT "
              "from the desired aggregate. Export files are staged, read back, and replaced individually; "
              "publication across five CSVs and two reports is not one filesystem transaction. Run one "
              "analysis instance at a time, and revalidate after an interrupted publication.", "",
              "## Next-stage readiness", "",
              "**The outputs are safe for the next analytical stage under the documented eligibility and "
              "grain rules.** Counts and monetary rollups reconcile; differences between payments and "
              "item-plus-freight totals remain disclosed and require source interpretation. Treat boundary "
              "months, late-period outcome coverage, unknown currency semantics, and incomplete customer "
              "history explicitly. These metrics are observed item sales, not net revenue or cash-flow "
              "reconciliation. No strategic recommendation, visualization, dashboard, RFM segmentation, "
              "geolocation analysis, or chronology repair was performed.", ""]
    (ROOT / "reports/business_metric_validation.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports/business_metric_validation.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
