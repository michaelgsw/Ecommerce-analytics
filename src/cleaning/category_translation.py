"""Normalize supplied category labels without inventing translations."""
from .common import standardize_text


def clean(frame):
    standardize_text(
        frame, ["product_category_name", "product_category_name_english"],
        case="lower", replace_spaces=True,
    )
    return frame
