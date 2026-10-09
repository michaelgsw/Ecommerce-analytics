"""Small helpers shared by the dataset-specific cleaners."""

from decimal import Decimal, InvalidOperation
import hashlib
import re

import pandas as pd


def file_hash(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def prepare_frame(raw):
    """Remove only identical source rows, preserving first-record lineage."""
    columns = [re.sub(r"\s+", "_", name.strip().lower()) for name in raw.columns]
    if len(set(columns)) != len(columns) or any(name.startswith("source_") for name in columns):
        raise ValueError("Ambiguous column names or reserved lineage columns in source.")
    duplicate_mask = raw.duplicated(keep="first")
    frame = raw.loc[~duplicate_mask].copy()
    frame.columns = columns
    # Parsed CSV record number after the header; multiline text is one record.
    frame["source_record_number"] = frame.index + 1
    for column in columns:
        values = frame[column].astype("string")
        blank = values.isna() | values.str.strip().eq("").fillna(False)
        frame[column] = values.mask(blank, pd.NA)
    frame = frame.reset_index(drop=True)
    details = {
        "original_rows": int(len(raw)),
        "original_duplicate_rows": int(duplicate_mask.sum()),
        "duplicates_removed": int(duplicate_mask.sum()),
        "removed_source_record_numbers": (raw.index[duplicate_mask] + 1).tolist(),
        "original_missing": {
            name: int(raw[name].astype("string").str.strip().eq("").fillna(True).sum())
            for name in raw.columns
        },
    }
    return frame, details


def standardize_text(frame, columns, case=None, replace_spaces=False):
    """Normalize structured labels only; review prose is deliberately untouched."""
    for column in columns:
        values = frame[column].str.strip()
        if case == "lower":
            values = values.str.lower()
        elif case == "upper":
            values = values.str.upper()
        if replace_spaces:
            values = values.str.replace(r"\s+", "_", regex=True)
        frame[column] = values


def parse_dates(frame, columns):
    for column in columns:
        values = frame[column].str.strip()
        valid_format = values.str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}").fillna(True)
        dates = pd.to_datetime(values, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        invalid = ~valid_format | (values.notna() & dates.isna())
        if invalid.any():
            raise ValueError(f"{column}: {int(invalid.sum())} invalid nonmissing timestamps; no output published.")
        frame[column] = dates


def parse_integers(frame, columns):
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce")
        invalid = frame[column].notna() & (values.isna() | values.mod(1).ne(0))
        if invalid.any():
            raise ValueError(f"{column}: invalid whole-number values; no output published.")
        frame[column] = values.astype("Int64")


def parse_money(frame, columns):
    """Keep exact decimal amounts in original units; do not assume currency."""
    for column in columns:
        amounts = []
        for value in frame[column]:
            if pd.isna(value):
                amounts.append(None)
                continue
            try:
                amount = Decimal(str(value).strip())
            except InvalidOperation as error:
                raise ValueError(f"{column}: invalid decimal amount {value!r}.") from error
            if not amount.is_finite() or amount < 0:
                raise ValueError(f"{column}: nonfinite or negative amount {value!r}.")
            amounts.append(amount)
        frame[column] = pd.Series(amounts, index=frame.index, dtype="object")


def earlier_than(frame, later_column, earlier_column):
    comparable = frame[later_column].notna() & frame[earlier_column].notna()
    return comparable & frame[later_column].lt(frame[earlier_column])
