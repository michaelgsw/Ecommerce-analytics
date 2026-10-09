"""Keep composite item keys and exact nonnegative price/freight amounts."""
from .common import parse_dates, parse_integers, parse_money, standardize_text
from .schema import DATES, INTEGERS, MONEY


def clean(frame):
    standardize_text(frame, ["order_id", "product_id", "seller_id"])
    parse_dates(frame, DATES["order_items"])
    parse_integers(frame, INTEGERS["order_items"])
    parse_money(frame, MONEY["order_items"])
    # Cross-table shipment date flags are added after orders have been cleaned.
    return frame
