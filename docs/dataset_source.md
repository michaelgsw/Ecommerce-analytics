# Dataset Source Record

## Source

- **Dataset:** Brazilian E-Commerce Public Dataset by Olist
- **Publisher:** Olist (`olistbr` on Kaggle)
- **Dataset page:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Download endpoint:** https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
- **Downloaded:** October 5, 2026 (America/New_York calendar date)
- **License listed on Kaggle:** CC BY-NC-SA 4.0
- **License reference:** https://creativecommons.org/licenses/by-nc-sa/4.0/

Retain source attribution and the listed license when documenting or sharing this
project. The download used the dataset's current default version; its version number
was not captured. The checksum below identifies the exact downloaded archive.

## Local files

All source files are in `data/raw/`, which is excluded from version control.
The original ZIP is preserved alongside the extracted, unchanged CSV files.

- `olist_brazilian_ecommerce.zip` — downloaded archive, 44,717,580 bytes
- `olist_customers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `product_category_name_translation.csv`

## Download verification

The Kaggle endpoint returned HTTP 200. The ZIP archive opened successfully, all nine
CSV files were extracted, and each extracted file's byte size matched its archive
entry. No pre-existing files were overwritten.

Archive SHA-256:

```text
967E41E04FC306FE604E2A693F488995A8B41E5047418F8A5C8E4ABD6DECA784
```

This original verification covers download and extraction only. Subsequent
structural profiling is documented in [the data dictionary](data_dictionary.md)
and [the profile summary](../reports/data_profile.md), with per-CSV hashes in
`data/processed/data_profile.json`. Subsequent prepared-CSV cleaning is documented
in [the cleaning report](../reports/cleaning_report.md); all raw bytes are preserved.
No business analysis has been performed; metric feasibility remains a later decision.
