

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