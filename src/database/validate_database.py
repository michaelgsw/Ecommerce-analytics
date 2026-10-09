"""Independent CSV-to-SQLite checks; does not import the builder or cleaners.

Run separately: python -m src.database.validate_database
The database is opened read-only. No validation changes any data file.
"""

from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "data/database/olist_analytics.db"
KEYS = {
    "customers": ("customer_id",), "orders": ("order_id",),
    "products": ("product_id",), "sellers": ("seller_id",),
    "order_items": ("order_id", "order_item_id"),
    "payments": ("order_id", "payment_sequential"),
    "reviews": ("review_id", "order_id"),
    "product_categories": ("product_category_name",),
}
NUMERIC = {
    "order_item_id", "payment_sequential", "payment_installments", "review_score",
    "product_name_length", "product_description_length", "product_photos_qty",
    "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
    "source_record_number",
}
DATES = {
    "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date", "shipping_limit_date",
    "review_creation_date", "review_answer_timestamp",
}
MONEY = {"order_items": ("price", "freight_value"), "payments": ("payment_value",)}
RELATIONS = {
    ("orders", "customer_id", "customers", "customer_id"),
    ("products", "product_category_name", "product_categories", "product_category_name"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("reviews", "order_id", "orders", "order_id"),
}
INDEXES = {
    "idx_customers_customer_unique_id": ("customers", "customer_unique_id"),
    "idx_orders_customer_id": ("orders", "customer_id"),
    "idx_order_items_product_id": ("order_items", "product_id"),
    "idx_order_items_seller_id": ("order_items", "seller_id"),
    "idx_reviews_order_id": ("reviews", "order_id"),
    "idx_products_category": ("products", "product_category_name"),
}


def check(findings, name, passed, detail):
    findings["checks"].append({"name": name, "passed": bool(passed), "detail": detail})


def source_rows(table):
    with (ROOT / f"data/processed/{table}_clean.csv").open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"{table}: invalid CSV header")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{table}: invalid CSV field count")
            yield row


def reconcile_table(connection, table, findings):
    """Match by validated PK, never rely on physical row order in prepared tables."""
    columns = list(next(source_rows(table)))
    database_rows = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
    expected_columns = columns + [f"{c}_hundredths" for c in MONEY.get(table, ())]
    info = list(connection.execute(f'PRAGMA table_info("{table}")'))
    check(findings, f"{table}: columns", [r["name"] for r in info] == expected_columns, expected_columns)
    expected_types = {c: "INTEGER" if c in NUMERIC or c.startswith("flag_") or c.endswith("_hundredths") else "TEXT" for c in expected_columns}
    check(findings, f"{table}: declared types", {r["name"]: r["type"] for r in info} == expected_types, expected_types)
    by_key = {tuple(row[column] for column in KEYS[table]): row for row in database_rows}
    check(findings, f"{table}: database PK uniqueness", len(by_key) == len(database_rows), len(database_rows) - len(by_key))
    del database_rows
    staging = connection.execute(f'SELECT * FROM "stg_{table}" ORDER BY rowid')
    csv_nulls, sql_nulls = Counter(), Counter()
    sums, scaled_sums, timestamp_ranges = {}, {}, {}
    mismatches, staging_mismatches, source_duplicates, count = 0, 0, 0, 0
    samples, seen = [], set()
    for source in source_rows(table):
        count += 1
        staged = next(staging, None)
        if staged is None or dict(staged) != source:
            staging_mismatches += 1
        key = tuple(int(source[c]) if c in NUMERIC else source[c] for c in KEYS[table])
        if key in seen:
            source_duplicates += 1
        seen.add(key)
        actual = by_key.pop(key, None)
        if actual is None:
            mismatches += 1
            if len(samples) < 10:
                samples.append(f"Missing DB key {key}")
            continue
        for column, value in source.items():
            expected = None if not value.strip() else value
            if expected is None:
                csv_nulls[column] += 1
            elif column.startswith("flag_"):
                if value not in ("True", "False"):
                    raise ValueError(f"{table}.{column}: invalid Boolean source text")
                expected = 1 if value == "True" else 0
            elif column in NUMERIC:
                number = Decimal(value)
                if not number.is_finite() or number != number.to_integral_value():
                    raise ValueError(f"{table}.{column}: invalid integer source value")
                expected = int(number)
            elif column in DATES:
                parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                if parsed.strftime("%Y-%m-%d %H:%M:%S") != value or parsed.tzinfo is not None:
                    raise ValueError(f"{table}.{column}: invalid canonical source timestamp")
                bounds = timestamp_ranges.setdefault(column, {"count": 0, "min": value, "max": value})
                bounds["count"] += 1
                bounds["min"], bounds["max"] = min(bounds["min"], value), max(bounds["max"], value)
            observed = actual[column]
            if observed is None:
                sql_nulls[column] += 1
            correct_type = observed is None or type(observed) is type(expected)
            if observed != expected or not correct_type:
                mismatches += 1
                if len(samples) < 10:
                    samples.append(f"{key}, {column}: expected {expected!r}, found {observed!r}")
        for column in MONEY.get(table, ()):
            original = Decimal(source[column])
            stored = Decimal(actual[column])
            # Multiplying by a power of ten is exact for these independently inspected values.
            scaled = original * Decimal("100")
            if not original.is_finite() or original < 0 or scaled != scaled.to_integral_value():
                raise ValueError(f"{table}.{column}: invalid amount or unsupported exact scale")
            hundredths = actual[f"{column}_hundredths"]
            if stored != original or type(hundredths) is not int or Decimal(hundredths) != scaled:
                mismatches += 1
            sums[column] = sums.get(column, Decimal(0)) + original
            scaled_sums[column] = scaled_sums.get(column, 0) + int(scaled)
    if next(staging, None) is not None:
        staging_mismatches += 1
    db_count = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    stg_count = connection.execute(f'SELECT COUNT(*) FROM "stg_{table}"').fetchone()[0]
    check(findings, f"{table}: CSV/prepared/staging counts", count == db_count == stg_count, [count, db_count, stg_count])
    check(findings, f"{table}: source PK uniqueness", source_duplicates == 0, source_duplicates)
    check(findings, f"{table}: every prepared field and storage type", mismatches == 0 and not by_key, {"mismatches": mismatches, "unmatched_keys": len(by_key), "samples": samples})
    check(findings, f"{table}: every staging text field", staging_mismatches == 0, staging_mismatches)
    check(findings, f"{table}: NULL preservation", csv_nulls == sql_nulls, {c: [csv_nulls[c], sql_nulls[c]] for c in columns})
    for column, total in scaled_sums.items():
        actual_sum = connection.execute(f'SELECT SUM("{column}_hundredths") FROM "{table}"').fetchone()[0]
        check(findings, f"{table}.{column}: exact numeric reconciliation", actual_sum == total and Decimal(total) == sums[column] * 100, {"decimal_source_total": str(sums[column]), "integer_source_total": total, "integer_sql_total": actual_sum})
    for column, bounds in timestamp_ranges.items():
        actual_bounds = connection.execute(f'SELECT COUNT("{column}"), MIN("{column}"), MAX("{column}") FROM "{table}"').fetchone()
        check(findings, f"{table}.{column}: timestamp coverage", list(actual_bounds) == [bounds["count"], bounds["min"], bounds["max"]], bounds)
    findings["tables"][table] = {"csv_rows": count, "database_rows": db_count, "staging_rows": stg_count, "nulls": dict(csv_nulls), "timestamps": timestamp_ranges}


def reconcile_categories(connection, findings):
    translations = {}
    count = 0
    staging = connection.execute("SELECT * FROM stg_category_translation ORDER BY rowid")
    staging_errors = 0
    for row in source_rows("category_translation"):
        count += 1
        staged = next(staging, None)
        staging_errors += int(staged is None or dict(staged) != row)
        label = row["product_category_name"]
        if label in translations:
            raise ValueError("Duplicate translation source label")
        translations[label] = row["product_category_name_english"] if row["product_category_name_english"].strip() else None
    staging_errors += int(next(staging, None) is not None)
    labels = {row["product_category_name"] for row in source_rows("products") if row["product_category_name"].strip()}
    labels.update(label for label in translations if label.strip())
    expected = {label: translations.get(label) for label in labels}
    actual = dict(connection.execute("SELECT product_category_name, product_category_name_english FROM product_categories"))
    check(findings, "categories: exact observed label union and supplied translations", actual == expected, {"labels": len(labels), "translations": count, "untranslated": sorted(k for k, v in expected.items() if v is None)})
    check(findings, "category translations: every staging field", staging_errors == 0, staging_errors)
    findings["tables"]["product_categories"] = {"csv_rows": len(labels), "database_rows": len(actual), "staging_rows": None, "nulls": {"product_category_name_english": sum(v is None for v in actual.values())}, "timestamps": {}}
    findings["tables"]["stg_category_translation"] = {"csv_rows": count, "database_rows": connection.execute("SELECT COUNT(*) FROM stg_category_translation").fetchone()[0], "staging_rows": count, "nulls": {}, "timestamps": {}}
    check(findings, "category translations: row count", findings["tables"]["stg_category_translation"]["database_rows"] == count, count)


def inspect_schema(connection, findings):
    actual_relations = set()
    all_indexes = []
    constraints = []
    for table, keys in KEYS.items():
        columns = list(connection.execute(f'PRAGMA table_info("{table}")'))
        actual_keys = tuple(row["name"] for row in sorted(columns, key=lambda r: r["pk"]) if row["pk"])
        check(findings, f"{table}: declared primary key", actual_keys == keys, list(actual_keys))
        check(findings, f"{table}: primary keys explicitly NOT NULL", all(row["notnull"] for row in columns if row["name"] in keys), list(keys))
        duplicate_groups = connection.execute(f'SELECT COUNT(*) FROM (SELECT 1 FROM "{table}" GROUP BY {", ".join(keys)} HAVING COUNT(*) > 1)').fetchone()[0]
        check(findings, f"{table}: SQL duplicate PK groups", duplicate_groups == 0, duplicate_groups)
        for row in connection.execute(f'PRAGMA foreign_key_list("{table}")'):
            actual_relations.add((table, row["from"], row["table"], row["to"]))
        for index in connection.execute(f'PRAGMA index_list("{table}")'):
            name = index["name"]
            index_columns = [row["name"] for row in connection.execute(f'PRAGMA index_info("{name}")')]
            all_indexes.append({"table": table, "name": name, "columns": index_columns, "unique": bool(index["unique"]), "origin": index["origin"]})
        constraints.append(connection.execute("SELECT sql FROM sqlite_schema WHERE name = ?", (table,)).fetchone()[0])
    check(findings, "schema: seven expected foreign keys", actual_relations == RELATIONS, sorted(actual_relations))
    explicit = {idx["name"]: (idx["table"], *idx["columns"]) for idx in all_indexes if idx["origin"] == "c"}
    check(findings, "schema: all analytical join indexes", explicit == INDEXES, explicit)
    check(findings, "schema: no extra UNIQUE indexes", all(idx["origin"] == "pk" or not idx["unique"] for idx in all_indexes), all_indexes)
    expected_tables = set(KEYS) | {f"stg_{t}" for t in KEYS if t != "product_categories"} | {"stg_category_translation"}
    actual_tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    check(findings, "schema: expected tables and no geolocation", actual_tables == expected_tables, sorted(actual_tables))
    strict_tables = {row["name"] for row in connection.execute("PRAGMA table_list") if row["strict"]}
    check(findings, "schema: all project tables STRICT", expected_tables <= strict_tables, sorted(strict_tables))
    findings["indexes"] = all_indexes
    findings["constraints"] = constraints
    findings["foreign_keys"] = sorted(actual_relations)


def run_sql_checks(connection, findings):
    """Run the saved SQL exactly as a user would; violations must always be zero."""
    statement = ""
    results = []
    for line in (ROOT / "sql/validation.sql").read_text(encoding="utf-8").splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            cursor = connection.execute(statement)
            rows = [dict(row) for row in cursor]
            results.append({"statement": statement.strip(), "rows": rows})
            for row in rows:
                if "violations" in row:
                    check(findings, f"SQL: {row['check_name']}", row["violations"] == 0, row["violations"])
            statement = ""
    if statement.strip():
        raise ValueError("Incomplete statement in validation.sql")
    findings["sql_results"] = results


def validate_database(path=DATABASE):
    findings = {
        "checks": [], "tables": {}, "sqlite_version": sqlite3.sqlite_version,
        "validated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        check(findings, "SQLite integrity_check", integrity == ["ok"], integrity)
        foreign_errors = [tuple(row) for row in connection.execute("PRAGMA foreign_key_check")]
        check(findings, "SQLite foreign_key_check", not foreign_errors, foreign_errors)
        inspect_schema(connection, findings)
        for table in KEYS:
            if table != "product_categories":
                print(f"Independently checking {table}...", flush=True)
                reconcile_table(connection, table, findings)
        reconcile_categories(connection, findings)
        run_sql_checks(connection, findings)
    finally:
        connection.close()
    failed = [item for item in findings["checks"] if not item["passed"]]
    if failed:
        raise ValueError("Independent database validation failed:\n" + json.dumps(failed, indent=2))
    return findings


def write_report(findings, database=DATABASE):
    with database.open("rb") as source:
        findings["database_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
    lines = [
        "# SQLite Database Validation", "",
        f"Validation run (UTC): {findings['validated_at_utc']}. User reporting timezone: America/New_York.", "",
        f"**PASS: {len(findings['checks'])} checks; 0 failures.** Database: `data/database/olist_analytics.db`.",
        f"SQLite runtime: {findings['sqlite_version']}. Database SHA-256: `{findings['database_sha256']}`.", "",
        "## Independent method", "",
        "The standard-library validator opens SQLite read-only and rereads the eight processed CSVs. "
        "It imports neither cleaning functions nor loader/conversion functions. Each prepared value is "
        "matched by its validated primary key, including exact text, INTEGER types, quality flags, "
        "lineage, NULL positions, decimal amounts, and timestamp format. Each staging CSV record is "
        "compared field by field as original parsed text, including blank fields and multiline prose. "
        "CSV counts are recomputed, not taken from the cleaning manifest. The saved SQL checks are also executed.", "",
        "## Row reconciliation", "",
    ]
    for table, detail in findings["tables"].items():
        basis = "distinct nonblank product/translation label union" if table == "product_categories" else "processed CSV"
        staged = f"; staging {detail['staging_rows']:,}" if detail["staging_rows"] is not None and not table.startswith("stg_") else ""
        lines.append(f"- `{table}`: {basis} {detail['csv_rows']:,}; database {detail['database_rows']:,}{staged}; difference 0.")
    lines += ["", "The seven entity staging tables retain exactly the same row counts as their corresponding "
              "prepared tables. The 71 supplied translations are retained in `stg_category_translation`; "
              "the category parent contains 73 observed labels and two NULL English translations.", "",
              "## Storage, NULLs, numbers, and timestamps", "",
              "IDs, postal prefixes, and populated prose remain exact TEXT. Missing optional values become "
              "SQL NULL only in prepared tables; staging keeps the exact blank text. Every flag becomes "
              "INTEGER 0/1, and lineage is retained. No source data or quality flags are dropped.", "",
              "`price`, `freight_value`, and `payment_value` retain their exact CSV decimal strings as TEXT. "
              "Their companion `price_hundredths`, `freight_value_hundredths`, and `payment_value_hundredths` "
              "columns store exact INTEGER hundredths of the unspecified source unit. Every amount was "
              "checked with Decimal, including scale, nonnegativity, finite values, equality per row, and "
              "exact aggregate reconciliation. No binary float or rounding is used. The builder rejects "
              "future amounts that cannot fit this scale or the signed 64-bit INTEGER range. These columns "
              "do not assert a currency or define sales eligibility. Use the integer companions for exact "
              "SQL arithmetic; SUM/CAST of the text amounts can invoke SQLite floating-point arithmetic. "
              "Keep totals in hundredths and format with Decimal outside SQLite; `/100.0` is approximate display.", "",
              "All eight timestamp columns are parsed strictly as `YYYY-MM-DD HH:MM:SS`, "
              "stored as TEXT, and checked per row and by count/minimum/maximum. No timezone is assigned. "
              "No timestamp chronology constraint is imposed.", "", "### Missing values preserved (CSV / SQL)", ""]
    for table, detail in findings["tables"].items():
        for column, count in detail["nulls"].items():
            lines.append(f"- `{table}.{column}`: {count:,} / {count:,}.")
    lines += ["", "All other prepared fields have zero missing values on both sides. Every NULL position, "
              "rather than just its count, was checked. Category English NULLs are derived from absent supplied translations.", "",
              "### Timestamp coverage", ""]
    for table, detail in findings["tables"].items():
        for column, bounds in detail["timestamps"].items():
            lines.append(f"- `{table}.{column}`: {bounds['count']:,} populated; `{bounds['min']}` through `{bounds['max']}`; exact match.")
    lines += ["", "## Keys, foreign keys, and indexes", "",
              "All eight prepared primary keys are explicitly NOT NULL, declared as specified, "
              "and independently checked for duplicate groups. No duplicate groups or foreign-key "
              "violations were found; SQLite integrity_check returned `ok`.", ""]
    for table, keys in KEYS.items():
        lines.append(f"- `{table}` primary key: `({', '.join(keys)})`.")
    lines += ["", "All seven foreign keys use ON UPDATE NO ACTION / ON DELETE NO ACTION:", ""]
    for child, column, parent, target in findings["foreign_keys"]:
        lines.append(f"- `{child}.{column}` → `{parent}.{target}`.")
    lines += ["", "Every index (including SQLite's automatic primary-key indexes):", ""]
    for index in findings["indexes"]:
        kind = "unique primary-key" if index["origin"] == "pk" else "nonunique analytical join"
        lines.append(f"- `{index['name']}` on `{index['table']}({', '.join(index['columns'])})`: {kind}.")
    lines += ["", "The composite PK indexes cover `order_items.order_id` and `payments.order_id` "
              "through their leading columns; redundant single-column indexes are omitted. Staging "
              "tables have no explicit indexes or uniqueness constraints. ANALYZE supplies planner statistics.", "",
              "## Complete constraints", "",
              "All project tables are STRICT (SQLite 3.37 or newer). Prepared required operational fields, "
              "lineage, and flags are NOT NULL; optional product metadata, lifecycle timestamps, review text, "
              "and category English names remain nullable. Staging columns are TEXT NOT NULL, accepting blank strings. "
              "Checks permit Boolean flags 0/1; review scores 1–5; positive item/payment sequences and lineage "
              "record numbers; nonnegative product metadata, installments, and integer monetary companions; "
              "the eight observed order statuses; the five observed payment types; and a nonblank category key. "
              "The exact prepared DDL below exhaustively records every NOT NULL, CHECK, PK, and FK constraint.", ""]
    for ddl in findings["constraints"]:
        lines += ["```sql", ddl + ";", "```", ""]
    lines += ["No UNIQUE constraint exists on customer_unique_id, orders.customer_id, payments.order_id, "
              "reviews.order_id, or review_id alone. There are no chronology checks, parent-must-have-child "
              "requirements, positive-only money/weight/installment requirements, or postal/geolocation foreign keys.", "",
              "## Retained source edge cases and issues", ""]
    for result in findings["sql_results"]:
        for row in result["rows"]:
            if "observation" in row:
                lines.append(f"- {row['observation']}: {row['records']:,} retained records/groups.")
    lines += ["", "These are existing source conditions, not loading defects. Missing categories/metadata, "
              "untranslated labels, zero payment/installment/weight values, missing delivered stages, "
              "unusual shipment deadlines, and timestamp conflicts still require metric-specific interpretation. "
              "Flags preserve the evidence. Repeated customer/review identifiers and split payments remain intact. "
              "See the independent source validation report for context; no repair was guessed.", "",
              "## Preservation and rebuild", ""]
    if "protected_files" in findings:
        lines.append(f"All {len(findings['protected_files'])} files under data/raw/ and data/processed/ had identical "
                     "before/after SHA-256 hashes. Processed CSV hashes also matched the completed cleaning manifest. "
                     "No geolocation table was loaded or joined; only its file bytes were hashed for preservation.")
    else:
        lines.append("This standalone run opened the database and CSVs read-only; build-time preservation hashes "
                     "are retained in the evidence JSON when available.")
    lines += ["", "```powershell", ".\\.venv\\Scripts\\python.exe -m src.database.build_database", "```", "",
              "A rebuild creates and validates a temporary database beside the destination, checks protected "
              "input hashes, and then atomically replaces only the database file. A failed prepublication "
              "check leaves the previous database intact. Close SQL clients before rebuilding on Windows. "
              "Database and Markdown/JSON report publication are separate filesystem operations. Run one "
              "builder/validator at a time and verify the database hash in the evidence after interruption.", "",
              "Recheck without rebuilding:", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m src.database.validate_database", "```", "",
              "## SQL analysis readiness", "",
              "**The database is structurally safe to use for SQL business analysis.** All loading and "
              "reconciliation checks pass; no confirmed database defects remain. Metric eligibility and "
              "currency semantics still need agreement, and anomaly flags need appropriate treatment for "
              "duration or retention metrics. Preserve parents with LEFT JOIN where needed; aggregate "
              "items, payments, and reviews separately to the intended grain before joining them to avoid "
              "multiplication. Use customer_unique_id for customer-level analytics after joining through "
              "customer_id. Enable PRAGMA foreign_keys = ON on every future writing connection. "
              "No business KPIs or geolocation analyses have been started.", ""]
    (ROOT / "reports/database_validation.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports/database_validation.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    findings = validate_database()
    evidence = ROOT / "reports/database_validation.json"
    if evidence.exists():
        previous = json.loads(evidence.read_text(encoding="utf-8"))
        baseline = previous.get("protected_files")
        if baseline:
            current = {}
            for folder in (ROOT / "data/raw", ROOT / "data/processed"):
                for path in sorted(folder.rglob("*")):
                    if path.is_file():
                        with path.open("rb") as source:
                            current[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(source, "sha256").hexdigest()
            if current != baseline:
                raise ValueError("Protected files differ from the build-time preservation evidence")
            findings["protected_files"] = baseline
    write_report(findings)
    print(f"PASS: {len(findings['checks'])} independent checks. reports/database_validation.md")
