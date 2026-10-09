"""Build a fresh database, validate it independently, then replace the old file.

Run from the project root: python -m src.database.build_database
Only data/database/ and reports/database_* outputs are written.
"""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .specification import (
    DATABASE, FILES, INTEGERS, LOAD_ORDER, MONEY, PROCESSED, ROOT,
    TIMESTAMP_FORMAT, TIMESTAMPS,
)


def protected_hashes():
    """Hash every protected file, including artifacts; never write to these folders."""
    result = {}
    for folder in (ROOT / "data/raw", PROCESSED):
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                with path.open("rb") as source:
                    result[path.relative_to(ROOT).as_posix()] = hashlib.file_digest(source, "sha256").hexdigest()
    return result


def quote(name):
    """Quote schema-controlled identifiers; CSV headers must match the static DDL."""
    return '"' + name.replace('"', '""') + '"'


def read_csv(table):
    path = PROCESSED / f"{table}_clean.csv"
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"{path.name}: missing or duplicate headers")
        for record, row in enumerate(reader, 1):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}: wrong field count at CSV record {record}")
            yield row


def scaled_hundredths(value):
    """Exact integer hundredths of an unspecified source unit, never float/cents."""
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid monetary value: {value!r}") from error
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"Nonfinite or negative money: {value!r}")
    # Give unusually long input enough precision to avoid Decimal context rounding.
    with localcontext() as context:
        context.prec = max(28, len(amount.as_tuple().digits) + 3)
        scaled = amount * 100
        if scaled != scaled.to_integral_value():
            raise ValueError(f"Money cannot be represented exactly in hundredths: {value!r}")
        integer = int(scaled)
    if not 0 <= integer <= 2**63 - 1:
        raise ValueError(f"Money exceeds SQLite's signed INTEGER range: {value!r}")
    return integer


def convert_value(column, value):
    if not value.strip():
        return None
    if column.startswith("flag_"):
        if value not in ("True", "False"):
            raise ValueError(f"{column}: expected True/False, got {value!r}")
        return int(value == "True")
    if column in INTEGERS:
        return int(value)
    if column in TIMESTAMPS:
        parsed = datetime.strptime(value, TIMESTAMP_FORMAT)
        if parsed.strftime(TIMESTAMP_FORMAT) != value:
            raise ValueError(f"{column}: timestamp is not in the canonical source format")
        return value  # No timezone assignment, conversion, or chronology repair.
    return value  # Preserve populated text, including whitespace in review prose.


def insert_rows(connection, table, columns, rows):
    sql = f"INSERT INTO {quote(table)} ({', '.join(map(quote, columns))}) VALUES ({', '.join('?' for _ in columns)})"
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) == 2000:
            connection.executemany(sql, batch)
            batch.clear()
    if batch:
        connection.executemany(sql, batch)


def stage_csv(connection, table, manifest):
    expected = list(manifest["tables"][table]["output_schema"])
    actual = [row[1] for row in connection.execute(f"PRAGMA table_info(stg_{table})")]
    if actual != expected:
        raise ValueError(f"{table}: manifest columns differ from static staging schema")

    def values():
        for row in read_csv(table):
            if list(row) != expected:
                raise ValueError(f"{table}: CSV headers differ from validated manifest")
            yield tuple(row[column] for column in expected)

    insert_rows(connection, f"stg_{table}", expected, values())


def load_categories(connection):
    """Union observed product/lookup labels; only supplied English text is used."""
    connection.execute("""
        INSERT INTO product_categories(product_category_name, product_category_name_english)
        SELECT labels.product_category_name, NULLIF(TRIM(t.product_category_name_english), '')
        FROM (
            SELECT product_category_name FROM stg_products WHERE TRIM(product_category_name) <> ''
            UNION
            SELECT product_category_name FROM stg_category_translation WHERE TRIM(product_category_name) <> ''
        ) AS labels
        LEFT JOIN stg_category_translation AS t USING(product_category_name)
    """)


def load_prepared(connection, table):
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info(stg_{table})")]
    money = MONEY.get(table, ())
    output_columns = columns + [f"{column}_hundredths" for column in money]

    def values():
        for row in read_csv(table):
            try:
                result = [convert_value(column, row[column]) for column in columns]
                result.extend(scaled_hundredths(row[column]) for column in money)
                yield tuple(result)
            except ValueError as error:
                raise ValueError(f"{table}, source record {row['source_record_number']}: {error}") from error

    insert_rows(connection, table, output_columns, values())


def build_database():
    before = protected_hashes()
    manifest = json.loads((PROCESSED / "cleaning_manifest.json").read_text(encoding="utf-8"))
    for table in FILES:
        relative = f"data/processed/{table}_clean.csv"
        if before[relative] != manifest["tables"][table]["output_sha256"]:
            raise ValueError(f"{relative}: bytes do not match the completed cleaning manifest")

    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive, unique temporary file in the destination directory; old DB survives failure.
    descriptor, temporary_name = tempfile.mkstemp(prefix="olist_build_", suffix=".db", dir=DATABASE.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    connection = None
    try:
        with sqlite3.connect(temporary) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
            connection.execute("BEGIN")
            for table in FILES:
                stage_csv(connection, table, manifest)
            load_categories(connection)
            for table in LOAD_ORDER:
                print(f"Loading {table}...", flush=True)
                load_prepared(connection, table)
            connection.execute("ANALYZE")
            connection.commit()
        # sqlite3's context manager commits/rolls back; explicitly close before Windows rename.
        connection.close()
        from .validate_database import validate_database, write_report
        findings = validate_database(temporary)
        if before != protected_hashes():
            raise ValueError("Protected raw/processed file hashes changed during the build")
        findings["protected_files"] = before
        os.replace(temporary, DATABASE)
        write_report(findings, DATABASE)
        print(f"Built and independently validated: {DATABASE}")
        for table, detail in findings["tables"].items():
            print(f"  {table}: {detail['database_rows']:,} rows")
        print(f"Validation report: {ROOT / 'reports/database_validation.md'}")
    finally:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    build_database()
