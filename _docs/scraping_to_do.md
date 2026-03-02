
  ---
  Moderate Issues

  7. _get_standardized_sizes has a Django import mid-method
  product_normalizer.py:139

  def _get_standardized_sizes(self) -> list:
      from data_management.utils.size_comparer import SizeComparer

  The import is placed AFTER the docstring (which itself comes after the def line — unusual). More importantly, this creates a hard dependency on
  data_management (a Django app) inside a class that's conceptually pure-Python normalization logic. For your tests, this means you either need the
  full Django app context set up, or you'll need to mock SizeComparer at this import path. This will make the normalization tests more painful than
  they need to be.

  8. _clean_value deduplicates words — affects products with intentional repetition
  product_normalizer.py:44

  words = sorted(list(set(value.split())))

  set() removes duplicate words before sorting. A product like "Mini Mini Wheats" becomes "mini wheats" — which may or may not be what you want for
  the dedup key. This is intentional for the bag-of-words approach, but it means two products that differ only by the repetition of a word would
  produce the same normalized_name_brand_size. Worth being aware of when writing tests.

  9. 1000g and 1000ml aren't normalized to "1kg" / "1l" in unit standardization
  BaseDataCleaner.py:185-196

  if unit == 'g' and quantity != 1000:
      ...  # converts to 1kg

  If a store sends a unit price string like "$X per 1000g", the quantity equals 1000 and the condition is False. final_measure stays as "1000g"
  instead of "1kg". Same for 1000ml → "1000ml" instead of "1l". In practice none of the four stores seem to send 1000g, but it's a gap that breaks
  the invariant "per-unit prices are always normalized to 1kg or 1L."

  10. Coles category path ordering
  DataCleanerColes.py:52-57

  category_path = [
      heir_list.get('subCategory'),   # → "Meat & Seafood"
      heir_list.get('category'),      # → "Lamb"
      heir_list.get('aisle'),         # → "Graze Grass-Fed Lamb"
  ]

  From the raw data onlineHeirs[0] has subCategory = "Meat & Seafood", category = "Lamb", aisle = "Graze Grass-Fed Lamb". The resulting path is
  ["Meat & Seafood", "Lamb", "Graze Grass-Fed Lamb"] — broad → narrow. The naming is confusing: subCategory is the top-level department and aisle is
   the most specific. The category hierarchy is inverted from what the field names suggest. Check this against how other stores build their category
   paths to confirm consistent ordering.

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
