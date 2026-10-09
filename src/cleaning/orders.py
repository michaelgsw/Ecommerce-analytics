"""Parse lifecycle dates; retain missing stages and flag temporal conflicts."""
from .common import earlier_than, parse_dates, standardize_text
from .schema import DATES


def clean(frame):
    standardize_text(frame, ["order_id", "customer_id"])
    standardize_text(frame, ["order_status"], case="lower")
    parse_dates(frame, DATES["orders"])
    pairs = {
        "flag_approval_before_purchase": ("order_approved_at", "order_purchase_timestamp"),
        "flag_carrier_before_purchase": ("order_delivered_carrier_date", "order_purchase_timestamp"),
        "flag_carrier_before_approval": ("order_delivered_carrier_date", "order_approved_at"),
        "flag_delivery_before_purchase": ("order_delivered_customer_date", "order_purchase_timestamp"),
        "flag_delivery_before_carrier": ("order_delivered_customer_date", "order_delivered_carrier_date"),
    }
    for name, (later, earlier) in pairs.items():
        frame[name] = earlier_than(frame, later, earlier)
    delivered = frame["order_status"].eq("delivered")
    for column in ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date"]:
        frame[f"flag_delivered_missing_{column}"] = delivered & frame[column].isna()
    return frame
