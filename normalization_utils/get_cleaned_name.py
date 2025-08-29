import re

# Safely import the translation table
try:
    from api.data.product_name_translation_table import PRODUCT_NAME_TRANSLATIONS
except (ImportError, SyntaxError):
    PRODUCT_NAME_TRANSLATIONS = {}

def get_cleaned_name(name, brand, sizes):
    name_to_clean = name

    # Step 1: Use the translation table to find the canonical name
    if PRODUCT_NAME_TRANSLATIONS and name in PRODUCT_NAME_TRANSLATIONS:
        name_to_clean = PRODUCT_NAME_TRANSLATIONS[name]

    # Step 2: Remove brand from name
    if brand and brand.lower() in name_to_clean.lower():
        name_to_clean = re.sub(r'\b' + re.escape(brand) + r'\b', '', name_to_clean, flags=re.IGNORECASE).strip()
    
    # Step 3: Remove all identified size strings from the name
    if sizes:
        for s in sizes:
            name_to_clean = name_to_clean.replace(s, '').strip()

    # Step 4: A more general regex to remove any remaining size-like patterns
    units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
    size_pattern = r'\b\d+\.?\d*\s*(' + '|'.join(units) + r')s?\b'
    name_to_clean = re.sub(size_pattern, '', name_to_clean, flags=re.IGNORECASE)
    
    # Step 5: Clean up extra spaces that might be left after removal
    name_to_clean = re.sub(r'\s+', ' ', name_to_clean).strip()
    return name_to_clean
