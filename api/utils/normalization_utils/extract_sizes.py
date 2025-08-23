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

    # 4. Standard, simple sizes (e.g., "500g", "5 pack", "each") - the fallback
    optional_number_pattern = r'(\d+\.?\d*)?\s*(' + '|'.join(all_unit_variations) + r')\b'
    for match in re.finditer(optional_number_pattern, processed_text):
        sizes.add(re.sub(r'(\d)\s+([a-zA-Z])', r'\1\2', match.group(0).strip()))

    return list(sizes)