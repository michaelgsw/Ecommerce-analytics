"""Retain missing product metadata and measurements without imputation."""
from .common import parse_integers, standardize_text
from .schema import INTEGERS


def clean(frame):
    frame = frame.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    standardize_text(frame, ["product_id"])
    standardize_text(frame, ["product_category_name"], case="lower", replace_spaces=True)
    parse_integers(frame, INTEGERS["products"])
    frame["flag_category_missing"] = frame["product_category_name"].isna()
    frame["flag_weight_zero"] = frame["product_weight_g"].eq(0).fillna(False)
    return frame
