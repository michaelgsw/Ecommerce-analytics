"""Preserve multiple payment records and flag uninterpreted zero values."""
from decimal import Decimal

from .common import parse_integers, parse_money, standardize_text
from .schema import INTEGERS, MONEY


def clean(frame):
    standardize_text(frame, ["order_id"])
    standardize_text(frame, ["payment_type"], case="lower")
    parse_integers(frame, INTEGERS["payments"])
    parse_money(frame, MONEY["payments"])
    frame["flag_installments_zero"] = frame["payment_installments"].eq(0).fillna(False)
    frame["flag_payment_value_zero"] = frame["payment_value"].eq(Decimal("0"))
    frame["flag_payment_type_undefined"] = frame["payment_type"].eq("not_defined")
    return frame
