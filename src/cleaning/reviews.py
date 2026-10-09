"""Preserve all review/order pairs, scores, and populated review prose."""
from .common import earlier_than, parse_dates, parse_integers, standardize_text
from .schema import DATES, INTEGERS


def clean(frame):
    standardize_text(frame, ["review_id", "order_id"])
    parse_dates(frame, DATES["reviews"])
    parse_integers(frame, INTEGERS["reviews"])
    frame["flag_title_missing"] = frame["review_comment_title"].isna()
    frame["flag_message_missing"] = frame["review_comment_message"].isna()
    frame["flag_answer_before_creation"] = earlier_than(frame, "review_answer_timestamp", "review_creation_date")
    # Nonblank comments retain original whitespace, punctuation, accents, and lines.
    return frame
