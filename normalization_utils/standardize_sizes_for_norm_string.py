import re

def standardize_sizes_for_norm_string(sizes):
    """
    Standardizes a list of size strings for use in the normalization key.
    e.g., ["each", "1 pack", "500g"] -> ["1ea", "1pk", "500g"]
    """
    if not sizes:
        return []

    units = {
        'g': ['g', 'gram', 'grams'],
        'kg': ['kg', 'kilogram', 'kilograms'],
        'ml': ['ml', 'millilitre', 'millilitres'],
        'l': ['l', 'litre', 'litres'],
        'pk': ['pk', 'pack', 'packs'],
        'ea': ['each', 'ea'],
    }
    unit_map = {variation: standard for standard, variations in units.items() for variation in variations}

    standardized = set()
    for s in sizes:
        s_lower = s.lower().replace(" ", "")
        
        # Find the unit part first
        unit_str_found = None
        for unit_variation in unit_map.keys():
            if s_lower.endswith(unit_variation):
                unit_str_found = unit_variation
                break
        
        if not unit_str_found:
            standardized.add(s_lower)
            continue

        # Extract number part
        number_part = s_lower.replace(unit_str_found, '')
        number = "1" if not number_part else number_part

        standard_unit = unit_map[unit_str_found]
        standardized.add(f"{number}{standard_unit}")

    return sorted(list(standardized))
