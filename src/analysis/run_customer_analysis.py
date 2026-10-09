"""Read-only customer segmentation, value, repeat timing, and cohort analysis.

Run: python -m src.analysis.run_customer_analysis
Recheck compact exports: python -m src.analysis.run_customer_analysis --validate-only
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path

from .customer_queries import execute_customer_queries
from .run_analysis import (
    DATABASE, OUTPUT, QUERIES, ROOT, add_decimal_displays, check_csv_files,
    decimal_ratio, protected_hashes, write_csv_files,
)
from .validate_customer_analysis import validate_customer_analysis


def input_hashes():
    """Include all five prior exports as protected inputs; do not overwrite them."""
    hashes = protected_hashes()
    for name in QUERIES:
        path = OUTPUT / f"{name}.csv"
        with path.open("rb") as source:
            hashes[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(source, "sha256").hexdigest()
    return hashes


def retention_matrix(rows):
    """Compact wide table with per-cell coverage, observed counts and eligible rates."""
    cohorts = {}
    for source in rows:
        cohort = source["cohort_month"]
        row = cohorts.setdefault(cohort, {"cohort_month": cohort, "new_customers": source["new_customers"]})
        month = f"month_{source['month_index']}"
        row[f"{month}_observed_customers"] = source["observed_customers"]
        row[f"{month}_returning_customers"] = source["returning_customers_for_rate"]
        row[f"{month}_retention_percent"] = decimal_ratio(source["retention_percent_numerator"], source["retention_percent_denominator"])
        row[f"{month}_coverage"] = source["coverage_status"]
    return list(cohorts.values())


def main(validate_only=False):
    before = input_hashes()
    database_evidence = json.loads((ROOT / "reports/database_validation.json").read_text(encoding="utf-8"))
    prior = json.loads((ROOT / "reports/business_metric_validation.json").read_text(encoding="utf-8"))
    if before["data/database/olist_analytics.db"] != database_evidence["database_sha256"]:
        raise ValueError("Database differs from independently validated file")
    for name in QUERIES:
        if before[f"data/analytics/{name}.csv"] != prior["export_hashes"][f"{name}.csv"]:
            raise ValueError(f"Prior validated export changed: {name}.csv")
    connection = sqlite3.connect(DATABASE.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("BEGIN")
        results, prefix, query_hashes = execute_customer_queries(connection)
        findings = validate_customer_analysis(connection, results, prefix, prior["results"]["customer_overview"][0])
    finally:
        connection.close()
    formatted = {name: add_decimal_displays(rows) for name, rows in results.items()}
    exports = {
        "customer_segments": formatted["customer_segments"],
        "customer_cohort_summary": formatted["customer_cohort_summary"],
        "cohort_retention_matrix": retention_matrix(results["cohort_retention_long"]),
        "repeat_purchase_summary": formatted["repeat_purchase_summary"],
    }
    if before != input_hashes():
        raise ValueError("A protected database/schema/source/prior-export file changed")
    if validate_only:
        check_csv_files(OUTPUT, exports)
    else:
        with tempfile.TemporaryDirectory(prefix="customer_analysis_", dir=OUTPUT) as temporary:
            folder = Path(temporary)
            write_csv_files(folder, exports)
            check_csv_files(folder, exports)
            for name in exports:
                os.replace(folder / f"{name}.csv", OUTPUT / f"{name}.csv")
    findings.update({"validated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "protected_hashes": before, "query_hashes": query_hashes, "results": formatted,
                     "export_rows": {name: len(rows) for name, rows in exports.items()}, "export_hashes": {}})
    for name in exports:
        with (OUTPUT / f"{name}.csv").open("rb") as source:
            findings["export_hashes"][f"{name}.csv"] = hashlib.file_digest(source, "sha256").hexdigest()
    from .customer_reporting import write_customer_reports
    write_customer_reports(findings)
    print(f"PASS: {len(findings['checks'])} customer-analysis checks and four CSV readbacks.")
    print("Protected data/schema/database and five prior exports unchanged; no identifier-level exports.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true")
    main(parser.parse_args().validate_only)
