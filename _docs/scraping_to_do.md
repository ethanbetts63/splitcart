  1. ProductNormalizer is instantiated per product, and rebuilds regex patterns on every call

  _extract_sizes_from_string builds unit_map, all_unit_variations, and compiles all the regex patterns from scratch on every single product. In a
  50,000 product scrape that's 50,000 redundant compilations of the same patterns. They should be class-level constants compiled once.

  2. Silent failures in several critical paths

  _load_translation_tables swallows SyntaxError and ValueError silently with pass. If a translation table file is corrupt you proceed with empty
  dicts — meaning all cross-store product matching is silently broken for the entire run. Should at minimum log a warning. Same pattern in
  _extract_sizes_from_string — the regex failures produce empty results without any indication something went wrong.

  3. _is_valid_product is trivially weak for most stores

  The base implementation is return raw_product is not None. An empty dict {} passes. Coles overrides this correctly by checking _type == 'PRODUCT'.
   Woolworths, ALDI, and IGA have no structural validation whatsoever on the raw product before attempting to clean it.

  4. The dead branch in DataCleanerColes

  if isinstance(heir_list, list):
      category_path = [heir.get('name') for heir in heir_list if heir.get('name')]

  heir_list is online_heirs[0] — the first element of the onlineHeirs array. From the actual API data, onlineHeirs is always a list of dicts, so
  onlineHeirs[0] is always a dict. The isinstance(heir_list, list) branch can never be reached. Either the API can return a nested list structure
  that isn't in the sample data (and should be documented), or this is dead code that should be removed.

  5. INVALID_CATEGORIES is a one-entry hardcoded set

  INVALID_CATEGORIES = {"Footy Finals Kiosk"}

  This was clearly added reactively to handle one specific Woolworths promotional category. Hardcoded at class level with no comment explaining why.
   Should be a config value or at minimum have a comment. There will be more of these over time.

  6. IGA bypasses the base unit price mechanism entirely

  IGA manually calculates per_unit_price_value and per_unit_price_measure from raw numeric fields and then calls _get_standardized_unit_price_info.
  Every other store relies on PriceNormalizer to extract the value from the string. The IGA approach is actually more reliable (numeric fields are
  always more trustworthy than parsing strings), which raises the question of why the other stores don't do it the same way. The answer is probably
  "the other APIs don't give us clean numeric fields" — but it means the unit price pipeline has two effectively different code paths that need to
  be tested independently.