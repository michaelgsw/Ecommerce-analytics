"""Run all cleaners: python -m src.cleaning.run_cleaning [--overwrite]."""

import argparse
import importlib
import json
import logging
from pathlib import Path
import platform
import sys
import tempfile

import pandas as pd

from .common import file_hash, prepare_frame
from .reporting import make_report
from .schema import DATES, EXPECTED_COLUMNS, FILES, MONEY
from .validation import add_relationship_flags, validate_relationships, validate_table, verify_csv_round_trip

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def table_summary(frame, details, name):
    details["processed_rows"] = int(len(frame))
    details["processed_duplicate_rows"] = int(frame.duplicated(EXPECTED_COLUMNS[name]).sum())
    details["processed_missing"] = {column: int(frame[column].isna().sum()) for column in EXPECTED_COLUMNS[name]}
    details["flags"] = {column: int(frame[column].sum()) for column in frame.columns if column.startswith("flag_")}
    schema = {}
    for column in frame.columns:
        logical_type = str(frame[column].dtype)
        if column in MONEY.get(name, []):
            logical_type = "exact decimal in source currency units"
        elif column in DATES.get(name, []):
            logical_type = "timestamp serialized as YYYY-MM-DD HH:MM:SS; timezone unspecified"
        schema[column] = {"type": logical_type, "missing_count": int(frame[column].isna().sum())}
    details["output_schema"] = schema
    return details


def run_pipeline(overwrite=False):
    raw_directory = PROJECT_ROOT / "data" / "raw"
    output_directory = PROJECT_ROOT / "data" / "processed"
    report_path = PROJECT_ROOT / "reports" / "cleaning_report.md"
    output_paths = [output_directory / f"{name}_clean.csv" for name in FILES]
    manifest_path = output_directory / "cleaning_manifest.json"
    targets = output_paths + [manifest_path, report_path]
    existing = [str(path.relative_to(PROJECT_ROOT)) for path in targets if path.exists()]
    if existing and not overwrite:
        raise FileExistsError("Outputs already exist; use --overwrite to intentionally regenerate: " + ", ".join(existing))
    for target in targets:
        if target.resolve().is_relative_to(raw_directory.resolve()):
            raise ValueError("Output location must not be inside data/raw/.")
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(path for path in raw_directory.iterdir() if path.is_file())
    before_hashes = {path.name: file_hash(path) for path in source_paths}
    summary = {
        "python_version": platform.python_version(), "pandas_version": pd.__version__,
        "source_hashes": before_hashes, "tables": {}, "checks": [],
    }
    tables = {}
    try:
        for name, filename in FILES.items():
            logging.info("Reading and cleaning %s", filename)
            raw = pd.read_csv(raw_directory / filename, dtype="string", keep_default_na=False, encoding="utf-8-sig")
            frame, details = prepare_frame(raw)
            cleaner = importlib.import_module(f"src.cleaning.{name}")
            frame = cleaner.clean(frame)
            frame["source_file"] = filename
            summary["checks"].extend(validate_table(name, frame, details))
            tables[name] = frame
            summary["tables"][name] = details
            logging.info("%s: %s original rows, %s retained, %s exact duplicates removed", name, len(raw), len(frame), details["duplicates_removed"])
        summary["checks"].extend(validate_relationships(tables))
        logging.info("Checking geolocation prefix coverage; geographic cleaning remains deferred")
        geolocation = pd.read_csv(
            raw_directory / "olist_geolocation_dataset.csv", usecols=["geolocation_zip_code_prefix"],
            dtype="string", keep_default_na=False, encoding="utf-8-sig",
        )
        add_relationship_flags(tables, set(geolocation["geolocation_zip_code_prefix"]))
        for name, frame in tables.items():
            summary["tables"][name] = table_summary(frame, summary["tables"][name], name)
            flagged = int(frame.filter(regex="^flag_").any(axis=1).sum())
            logging.info("%s: %s rows have at least one review/coverage flag; records retained", name, flagged)
        logging.info("All %s required checks passed; staging and verifying CSV outputs", len(summary["checks"]))
        with tempfile.TemporaryDirectory(prefix=".cleaning-", dir=output_directory) as staging:
            staging_path = Path(staging)
            for name, frame in tables.items():
                staged = staging_path / f"{name}_clean.csv"
                frame.to_csv(staged, index=False, na_rep="", date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", lineterminator="\n")
                verify_csv_round_trip(staged, frame)
                summary["tables"][name]["output_sha256"] = file_hash(staged)
            after_hashes = {path.name: file_hash(path) for path in raw_directory.iterdir() if path.is_file()}
            if before_hashes != after_hashes:
                raise RuntimeError("Raw directory contents changed during cleaning; no outputs published.")
            summary["raw_files_unchanged"] = True
            summary["checks"].append({"check": "all raw source hashes unchanged", "passed": True})
            summary["checks"].append({"check": "all eight CSVs round-trip exactly", "passed": True})
            (staging_path / manifest_path.name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
            (staging_path / report_path.name).write_text(make_report(summary), encoding="utf-8")
            # Publish only after every table and serialized file passed validation.
            for name in FILES:
                (staging_path / f"{name}_clean.csv").replace(output_directory / f"{name}_clean.csv")
            (staging_path / report_path.name).replace(report_path)
            # Manifest is last; its output hashes identify one completed run.
            (staging_path / manifest_path.name).replace(manifest_path)
        logging.info("Published eight clean CSVs, manifest, and reports/cleaning_report.md")
        return summary
    finally:
        after_hashes = {path.name: file_hash(path) for path in raw_directory.iterdir() if path.is_file()}
        if before_hashes != after_hashes:
            raise RuntimeError("Raw directory contents changed during the run.")


def main():
    if Path(sys.prefix).resolve() != (PROJECT_ROOT / ".venv").resolve():
        raise SystemExit("Use the project's virtual environment: .venv/Scripts/python.exe -m src.cleaning.run_cleaning")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Regenerate only the pipeline's clean CSVs, manifest, and report; source files remain unchanged.")
    arguments = parser.parse_args()
    log_path = PROJECT_ROOT / "data" / "processed" / "cleaning.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, mode="a", encoding="utf-8")],
    )
    try:
        run_pipeline(overwrite=arguments.overwrite)
    except Exception:
        logging.exception("Cleaning failed; review the error. Raw files are never written by this pipeline.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
