import re
from .extract_sizes import extract_sizes

def get_cleaned_name(name, brand, sizes):
    name_to_clean = name
    # Remove brand from name
    if brand and brand.lower() in name_to_clean.lower():
        name_to_clean = re.sub(r'\b' + re.escape(brand) + r'\b', '', name_to_clean, flags=re.IGNORECASE).strip()
    
    # Remove all identified size strings from the name
    if sizes:
        for s in sizes:
            name_to_clean = name_to_clean.replace(s, '').strip()

    # A more general regex to remove any remaining size-like patterns
    units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
    size_pattern = r'\b\d+\.?\d*\s*(' + '|'.join(units) + r')s?\b'
    name_to_clean = re.sub(size_pattern, '', name_to_clean, flags=re.IGNORECASE)
    
    # Clean up extra spaces that might be left after removal
    name_to_clean = re.sub(r'\s+', ' ', name_to_clean).strip()
    return name_to_clean