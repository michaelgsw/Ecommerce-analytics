"""Read complete SQL statements grouped by human-readable result comments."""

import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "sql/analysis"
FILES = ("06_customer_value.sql", "07_customer_segments.sql", "08_customer_cohorts.sql", "09_repeat_purchase_behavior.sql")


def execute_customer_queries(connection):
    prefix = (FOLDER / "customer_level_aggregates.sql").read_text(encoding="utf-8").strip()
    cohort = (FOLDER / "customer_cohort_aggregates.sql").read_text(encoding="utf-8").strip()
    results, hashes = {}, {}
    for filename in FILES:
        text = (FOLDER / filename).read_text(encoding="utf-8")
        hashes[filename] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        sections = re.split(r"(?m)^-- result: ([a-z0-9_]+)\s*\n", text)
        if sections[0].strip() or len(sections) < 3:
            raise ValueError(f"{filename}: missing result-section comments")
        for name, query in zip(sections[1::2], sections[2::2]):
            if name in results:
                raise ValueError(f"Duplicate SQL result name: {name}")
            required_prefix = prefix + "\n" + cohort if filename == "08_customer_cohorts.sql" else prefix
            if not query.startswith(required_prefix + "\n"):
                raise ValueError(f"{filename}/{name}: shared customer/cohort CTE copy drifted")
            rows = [dict(row) for row in connection.execute(query)]
            if any(isinstance(value, float) for row in rows for value in row.values()):
                raise ValueError(f"{name}: unexpected binary-float analytical value")
            results[name] = rows
            print(f"Ran {filename}/{name}: {len(rows)} summary rows", flush=True)
    return results, prefix, hashes
