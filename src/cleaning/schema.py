"""Source files, field types, and required keys, based on the inspected dataset."""

FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

KEYS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "products": ["product_id"],
    "payments": ["order_id", "payment_sequential"],
    "reviews": ["review_id", "order_id"],
    "sellers": ["seller_id"],
    "category_translation": ["product_category_name"],
}

IDENTIFIERS = {
    "customers": ["customer_id", "customer_unique_id"],
    "orders": ["order_id", "customer_id"],
    "order_items": ["order_id", "product_id", "seller_id"],
    "products": ["product_id"],
    "payments": ["order_id"],
    "reviews": ["review_id", "order_id"],
    "sellers": ["seller_id"],
    "category_translation": [],
}

DATES = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

INTEGERS = {
    "order_items": ["order_item_id"],
    "products": [
        "product_name_length", "product_description_length", "product_photos_qty",
        "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
    ],
    "payments": ["payment_sequential", "payment_installments"],
    "reviews": ["review_score"],
}
MONEY = {"order_items": ["price", "freight_value"], "payments": ["payment_value"]}
ORDER_STATUSES = {
    "approved", "canceled", "created", "delivered", "invoiced", "processing",
    "shipped", "unavailable",
}
PAYMENT_TYPES = {"credit_card", "boleto", "voucher", "debit_card", "not_defined"}

# Required fields must exist and be populated. Optional attributes stay nullable.
REQUIRED = {
    "customers": IDENTIFIERS["customers"] + ["customer_zip_code_prefix", "customer_city", "customer_state"],
    "orders": IDENTIFIERS["orders"] + ["order_status", "order_purchase_timestamp", "order_estimated_delivery_date"],
    "order_items": IDENTIFIERS["order_items"] + ["order_item_id", "shipping_limit_date", "price", "freight_value"],
    "products": ["product_id"],
    "payments": ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
    "reviews": ["review_id", "order_id", "review_score", "review_creation_date", "review_answer_timestamp"],
    "sellers": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    "category_translation": ["product_category_name", "product_category_name_english"],
}

EXPECTED_COLUMNS = {
    "customers": REQUIRED["customers"],
    "orders": IDENTIFIERS["orders"] + ["order_status"] + DATES["orders"],
    "order_items": REQUIRED["order_items"],
    "products": ["product_id", "product_category_name"] + INTEGERS["products"],
    "payments": REQUIRED["payments"],
    "reviews": REQUIRED["reviews"] + ["review_comment_title", "review_comment_message"],
    "sellers": REQUIRED["sellers"],
    "category_translation": REQUIRED["category_translation"],
}

FOREIGN_KEYS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("reviews", "order_id", "orders", "order_id"),
]
