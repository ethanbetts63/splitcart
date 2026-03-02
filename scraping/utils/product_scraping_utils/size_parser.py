import re

_CONVERSION_MAP = {
    'g':  {'base': 'g',  'multiplier': 1.0},
    'kg': {'base': 'g',  'multiplier': 1000.0},
    'ml': {'base': 'ml', 'multiplier': 1.0},
    'l':  {'base': 'ml', 'multiplier': 1000.0},
    'pk': {'base': 'pk', 'multiplier': 1.0},
    'ea': {'base': 'ea', 'multiplier': 1.0},
}

_SIZE_PATTERN = re.compile(r"(\d+\.?\d*)\s*([a-z]+)$")


def parse_size(size_str: str) -> tuple | None:
    """
    Parses a standardized size string into a canonical (value, unit) tuple.
    Converts to base units: kg→g, l→ml.
    e.g., '1.5l' -> (1500.0, 'ml'), '500g' -> (500.0, 'g'), '0.11kg' -> (110.0, 'g')
    Returns None if the string cannot be parsed or the unit is unknown.
    """
    match = _SIZE_PATTERN.match(size_str)
    if not match:
        return None

    value_str, unit_str = match.groups()
    value = float(value_str)

    unit_info = _CONVERSION_MAP.get(unit_str)
    if not unit_info:
        return None

    canonical_value = value * unit_info['multiplier']
    return (canonical_value, unit_info['base'])
