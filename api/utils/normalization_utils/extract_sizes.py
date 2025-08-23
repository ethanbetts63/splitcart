import re

def extract_sizes(text):
    print(f"extract_sizes called with text: {text}")
    if not text:
        return []

    sizes = set()
    processed_text = text.lower()

    # Pre-process to remove common prefixes
    prefixes_to_remove = ['approx. ', 'approx ', 'around ', 'about ']
    for prefix in prefixes_to_remove:
        if processed_text.startswith(prefix):
            processed_text = processed_text[len(prefix):]

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

    # 4. Standard, simple sizes (e.g., "500g", "5 pack") - with numbers
    number_unit_pattern = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
    for match in re.finditer(number_unit_pattern, processed_text):
        unit = unit_map[match.group(2)]
        sizes.add(f"{match.group(1)}{unit}")
    processed_text = re.sub(number_unit_pattern, '', processed_text)
    
    # 5. Standalone units (e.g., "each") - no numbers
    # Exclude 'l' and other single-letter units that are too ambiguous
    standalone_units = [u for u in all_unit_variations if len(u) > 1] + ['ea'] # Keep 'ea'
    standalone_unit_pattern = r'\b(' + '|'.join(standalone_units) + r')\b'
    for match in re.finditer(standalone_unit_pattern, processed_text):
        unit = unit_map[match.group(1)]
        sizes.add(unit)

    return list(sizes)
