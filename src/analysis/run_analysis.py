"""Run read-only SQL, independently reconcile it, and publish compact CSVs.

Reproduce: python -m src.analysis.run_analysis
Recheck saved exports: python -m src.analysis.run_analysis --validate-only
All calculations use INTEGER or Decimal; no ORM, float, or schema changes.
"""

import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .validate_metrics import validate_metrics

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "data/database/olist_analytics.db"
SQL = ROOT / "sql/analysis"
OUTPUT = ROOT / "data/analytics"
QUERIES = {
    "sales_overview": "01_sales_overview.sql",
    "monthly_sales": "02_monthly_sales.sql",
    "category_performance": "03_product_performance.sql",
    "customer_overview": "04_customer_overview.sql",
    "order_status_summary": "05_order_operations.sql",
}


def protected_hashes():
    paths = [DATABASE, ROOT / "sql/schema.sql"]
    for folder in (ROOT / "data/raw", ROOT / "data/processed"):
        paths.extend(path for path in folder.rglob("*") if path.is_file())
    result = {}
    for path in sorted(paths):
        with path.open("rb") as source:
            result[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(source, "sha256").hexdigest()
    return result


def decimal_ratio(numerator, denominator):
    """Six-place display only; original integer rational components stay exported."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    if type(numerator) is not int or type(denominator) is not int:
        raise ValueError("A ratio component is not an exact integer")
    with localcontext() as context:
        context.prec = max(50, len(str(abs(numerator))) + len(str(abs(denominator))) + 10)
        ratio = Decimal(numerator) / Decimal(denominator)
        return format(ratio.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), "f")


def add_decimal_displays(rows):
    result = []
    for source in rows:
        row = dict(source)
        for column in source:
            if column.endswith("_numerator"):
                name = column.removesuffix("_numerator")
                row[name] = decimal_ratio(source[column], source[f"{name}_denominator"])
        result.append(row)
    return result


def execute_queries(connection):
    shared = (SQL / "order_level_aggregates.sql").read_text(encoding="utf-8").strip()
    results, query_hashes = {}, {}
    for name, filename in {**QUERIES, "sql_validation": "validation.sql"}.items():
        text = (SQL / filename).read_text(encoding="utf-8")
        if not text.startswith(shared + "\n"):
            raise ValueError(f"{filename}: shared CTE copy differs from order_level_aggregates.sql")
        results[name] = [dict(row) for row in connection.execute(text)]
        for row in results[name]:
            if any(isinstance(value, float) for value in row.values()):
                raise ValueError(f"{filename}: floating-point analytical result found")
        query_hashes[filename] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print(f"Ran {filename}: {len(results[name])} result rows", flush=True)
    return results, shared, query_hashes


def write_csv_files(folder, results):
    for name, rows in results.items():
        if not rows:
            raise ValueError(f"No result rows for {name}; output contract needs review")
        with (folder / f"{name}.csv").open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def check_csv_files(folder, results):
    """Reread serialized exports, including blank undefined ratios/NULL categories."""
    for name, rows in results.items():
        with (folder / f"{name}.csv").open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            observed = list(reader)
            columns = reader.fieldnames
        expected = [{key: "" if value is None else str(value) for key, value in row.items()} for row in rows]
        if columns != list(rows[0]) or observed != expected:
            raise ValueError(f"{name}.csv does not reconcile to validated query output")


def main(validate_only=False):
    before = protected_hashes()
    baseline = json.loads((ROOT / "reports/database_validation.json").read_text(encoding="utf-8"))
    if before["data/database/olist_analytics.db"] != baseline["database_sha256"]:
        raise ValueError("Database differs from its independent validation evidence; revalidate first")
    connection = sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")  # A consistent read snapshot across queries and checks.
        results, shared, query_hashes = execute_queries(connection)
        findings = validate_metrics(connection, results, shared)
    finally:
        connection.close()
    formatted = {name: add_decimal_displays(results[name]) for name in QUERIES}
    if before != protected_hashes():
        raise ValueError("Protected database, schema, or source file changed during analysis")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if validate_only:
        check_csv_files(OUTPUT, formatted)
    else:
        with tempfile.TemporaryDirectory(prefix="analysis_", dir=OUTPUT) as temporary:
            staging = Path(temporary)
            write_csv_files(staging, formatted)
            check_csv_files(staging, formatted)
            for name in QUERIES:
                os.replace(staging / f"{name}.csv", OUTPUT / f"{name}.csv")
    findings.update({
        "validated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protected_hashes": before, "query_hashes": query_hashes,
        "results": formatted, "export_rows": {name: len(rows) for name, rows in formatted.items()},
    })
    findings["export_hashes"] = {}
    for name in QUERIES:
        with (OUTPUT / f"{name}.csv").open("rb") as source:
            findings["export_hashes"][f"{name}.csv"] = hashlib.file_digest(source, "sha256").hexdigest()
    from .reporting import write_report
    write_report(findings)
    print(f"PASS: {len(findings['checks'])} metric checks plus 5 CSV readbacks; protected files unchanged.")
    print(f"Exports: {OUTPUT}")
    print(f"Report: {ROOT / 'reports/business_metric_validation.md'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="Reconcile existing CSVs without replacing them")
    main(parser.parse_args().validate_only)
