"""Preserve order-level customer records and persistent customer identities."""
from .common import standardize_text


def clean(frame):
    standardize_text(frame, ["customer_id", "customer_unique_id", "customer_zip_code_prefix"])
    standardize_text(frame, ["customer_city"], case="lower")
    standardize_text(frame, ["customer_state"], case="upper")
    # Never deduplicate on customer_unique_id: a customer may have many orders.
    return frame
