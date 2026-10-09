"""Standardize structured seller labels without inventing location mappings."""
from .common import standardize_text


def clean(frame):
    standardize_text(frame, ["seller_id", "seller_zip_code_prefix"])
    standardize_text(frame, ["seller_city"], case="lower")
    standardize_text(frame, ["seller_state"], case="upper")
    return frame
