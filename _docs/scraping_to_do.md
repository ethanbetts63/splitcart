
  13. Unparseable size deduplication uses .values() lookup
  product_normalizer.py:172

  if size_str not in canonical_sizes.values():
      canonical_sizes[('str', size_str)] = size_str

  This does a linear scan of all values to check for duplicates of the string representation. Since canonical_sizes.values() also contains the
  formatted strings of successfully parsed sizes (e.g., "500g"), this could theoretically prevent an unparseable size from being added if its string
   exactly matches a parsed size's formatted string. Practically unlikely, but the dedup keys for the two cases (tuple vs string) mean the real
  dedup should use ('str', size_str) as the key — which it does — so the .values() check is actually a secondary guard that's mostly redundant with
  the key check.

  14. scraped_date is set in both _post_process_product AND wrap_cleaned_products
  BaseDataCleaner.py:142 and wrap_cleaned_products.py:13

  The metadata wrapper independently computes and stores scraped_date. The product dict itself also has scraped_date set per-product. These should
  always be the same value (both from timestamp.date().isoformat()), but it's double-stored. If any product-level scraped_date differs from the
  metadata-level one, it would be confusing.
