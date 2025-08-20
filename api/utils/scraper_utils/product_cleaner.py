import re

def _clean_value(value):
    """Converts a value to a cleaned, lowercase string."""
    if value is None:
        return ''
    return str(value).strip().lower()

def normalize_product_data(product_data: dict) -> dict:
    """
    Applies a series of cleaning and normalization rules to a product data dictionary.
    This is intended to be a generic, final-step cleaner for all scrapers.

    - Renames 'package_size' to 'size' for consistency.
    - Cleans the 'size' field using a shared set of rules.
    - Generates the 'normalized_name_brand_size' key for de-duplication.
    """
    # --- Standardize size field name ---
    if 'package_size' in product_data and 'size' not in product_data:
        product_data['size'] = product_data.pop('package_size')

    size = product_data.get('size')

    # If there's no size to clean, just generate the key and return
    if not size or not isinstance(size, str):
        name = _clean_value(product_data.get('name'))
        brand = _clean_value(product_data.get('brand'))
        size_str = _clean_value(size)
        product_data['normalized_name_brand_size'] = f"{name}_{brand}_{size_str}"
        return product_data

    # --- Apply all the size cleaning rules ---
    new_size = size.lower().strip()

    # Rule Set 1: Normalization (e.g., remove spaces, prefixes)
    normalization_rules = {r'approx\.': '', r'(\d)\s+([a-zA-Z])': r'\1\2'}
    for pattern, replacement in normalization_rules.items():
        new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)

    # Rule Set 2: Unit Standardization (e.g., gram -> g)
    unit_rules = {r'\s*gram\s*': 'g', r'\s*litre\s*': 'lt', r'\s*pack\s*': 'pk', r'\s*kilo\s*': 'kg', r'\s*case\s*': 'pk', r'eachunit': 'each'}
    for pattern, replacement in unit_rules.items():
        new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)

    # Rule Set 3: Quantity Rules (e.g., 1 each -> each)
    quantity_rules = {r'1\s*each|1\.1\s*each': 'each'}
    for pattern, replacement in quantity_rules.items():
        new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)

    # Rule Set 4: Unit Conversions (e.g., 1.2l -> 1200ml)
    try:
        l_match = re.match(r'^(\d+\.?\d*)\s*l$', new_size)
        if l_match: new_size = f'{int(float(l_match.group(1)) * 1000)}ml'
        kg_match = re.match(r'^(\d+\.?\d*)\s*kg$', new_size)
        if kg_match: new_size = f'{int(float(kg_match.group(1)) * 1000)}g'
    except (ValueError, IndexError):
        pass # Keep size as is if conversion fails

    product_data['size'] = new_size.strip()

    # --- Generate the final normalized key ---
    name = _clean_value(product_data.get('name'))
    brand = _clean_value(product_data.get('brand'))
    size_str = _clean_value(product_data.get('size'))
    product_data['normalized_name_brand_size'] = f"{name}_{brand}_{size_str}"

    return product_data
