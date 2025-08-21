import re

def extract_sizes(text):
    if not text:
        return []

    sizes = set()
    processed_text = text.lower()

    units = {
        'g': ['g', 'gram', 'grams'],
        'kg': ['kg', 'kilogram', 'kilograms'],
        'ml': ['ml', 'millilitre', 'millilitres'],
        'l': ['l', 'litre', 'litres'],
        'pk': ['pk', 'pack', 'packs'],
        'ea': ['each', 'ea'],
    }
    
    unit_map = {variation: standard for standard, variations in units.items() for variation in variations}
    all_unit_variations = list(unit_map.keys())

    # --- Patterns are ordered from most specific to most general ---

    # 1. Ranges (e.g., "10-15kg", "400-500g")
    range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
    for match in re.finditer(range_pattern, processed_text):
        unit = unit_map[match.group(3)]
        sizes.add(f"{match.group(1)}{unit}")
        sizes.add(f"{match.group(2)}{unit}")
    processed_text = re.sub(range_pattern, '', processed_text)

    # 2. Multipacks (e.g., "4x250ml", "6 x 75g")
    multipack_pattern_1 = r'(\d+)\s*[xX]\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
    for match in re.finditer(multipack_pattern_1, processed_text):
        unit = unit_map[match.group(3)]
        sizes.add(f"{match.group(1)}pk")
        sizes.add(f"{match.group(2)}{unit}")
    processed_text = re.sub(multipack_pattern_1, '', processed_text)

    # 3. Multipacks - reversed (e.g., "250ml x 4", "75g x 6")
    multipack_pattern_2 = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\s*[xX]\s*(\d+)'
    for match in re.finditer(multipack_pattern_2, processed_text):
        unit = unit_map[match.group(2)]
        sizes.add(f"{match.group(1)}{unit}")
        sizes.add(f"{match.group(3)}pk")
    processed_text = re.sub(multipack_pattern_2, '', processed_text)

    # 4. Standard, simple sizes (e.g., "500g", "5 pack") - the fallback
    standard_pattern = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
    for match in re.finditer(standard_pattern, processed_text):
        unit = unit_map[match.group(2)]
        sizes.add(f"{match.group(1)}{unit}")

    return list(sizes)

def clean_value(value):
    if value is None:
        return ''
    words = sorted(str(value).lower().split())
    sorted_string = ' '.join(words)
    cleaned_value = re.sub(r'[^a-z0-9]', '', sorted_string)
    return cleaned_value

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

def normalize_product_data(product_instance):
    """
    Takes a Product instance, updates its sizes attribute, and calculates
    its normalized_name_brand_size.
    """
    # Extract sizes from name and brand
    name_sizes = extract_sizes(product_instance.name)
    brand_sizes = extract_sizes(product_instance.brand)

    # Combine with existing sizes, ensure uniqueness, and sort
    all_sizes = set(product_instance.sizes)
    all_sizes.update(name_sizes)
    all_sizes.update(brand_sizes)
    product_instance.sizes = sorted(list(all_sizes))

    # Calculate cleaned name
    cleaned_name = get_cleaned_name(product_instance.name, product_instance.brand, product_instance.sizes)

    # Generate normalized_name_brand_size
    normalized_string = clean_value(cleaned_name) + \
                        clean_value(product_instance.brand) + \
                        clean_value(" ".join(product_instance.sizes) if product_instance.sizes else "")
    
    return normalized_string
