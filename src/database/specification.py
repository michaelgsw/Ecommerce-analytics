"""Small, explicit mappings for the prepared CSV files (no cleaning imports)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
DATABASE = ROOT / "data" / "database" / "olist_analytics.db"

# Parents first; translations are staged before building the category parent.
LOAD_ORDER = ("customers", "sellers", "products", "orders", "order_items", "payments", "reviews")
FILES = (*LOAD_ORDER, "category_translation")
KEYS = {
    "customers": ("customer_id",), "orders": ("order_id",),
    "products": ("product_id",), "sellers": ("seller_id",),
    "order_items": ("order_id", "order_item_id"),
    "payments": ("order_id", "payment_sequential"),
    "reviews": ("review_id", "order_id"),
}
TIMESTAMPS = {
    "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
    "order_delivered_customer_date", "order_estimated_delivery_date",
    "shipping_limit_date", "review_creation_date", "review_answer_timestamp",
}
INTEGERS = {
    "source_record_number", "order_item_id", "payment_sequential", "payment_installments",
    "review_score", "product_name_length", "product_description_length",
    "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm",
    "product_width_cm",
}
MONEY = {"order_items": ("price", "freight_value"), "payments": ("payment_value",)}
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
