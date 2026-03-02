
  11. Woolworths category_path field map entry is a no-op
  DataCleanerWoolworths.py / field_maps.py:78

  The field map maps category_path to AdditionalAttributes.piesdepartmentnamesjson (a JSON string). But _transform_product immediately overwrites
  cleaned_product['category_path'] by reparsing all three JSON fields separately and combining them. The field map entry is never actually used for
  its mapped value. It only ensures the key exists in cleaned_product. This is a silent inconsistency — the field map suggests category_path comes
  from one field, but it actually comes from three.

  ---
  Minor Issues

  12. Duplicate 'ea' in standalone_units
  product_normalizer.py:102

  standalone_units = [u for u in all_unit_variations if len(u) > 1] + ['ea']

  'ea' already has length 2, so it's already included in the first part. The + ['ea'] adds it twice. Harmless but redundant.

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
