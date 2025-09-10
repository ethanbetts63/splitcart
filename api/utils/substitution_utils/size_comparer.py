import re
from api.utils.product_normalizer import ProductNormalizer

class SizeComparer:
    def __init__(self):
        self.conversion_map = {
            'g':  {'base': 'g',  'multiplier': 1.0},
            'kg': {'base': 'g',  'multiplier': 1000.0},
            'ml': {'base': 'ml', 'multiplier': 1.0},
            'l':  {'base': 'ml', 'multiplier': 1000.0},
            'pk': {'base': 'pk', 'multiplier': 1.0},
            'ea': {'base': 'ea', 'multiplier': 1.0},
        }
        # This regex is designed to capture a number (integer or float)
        # and an optional unit from the end of a string.
        self.size_pattern = re.compile(r"(\d+\.?\d*)\s*([a-z]+)$")

    def _parse_size(self, size_str: str) -> tuple | None:
        """
        Parses a standardized size string into a canonical (value, unit) tuple.
        e.g., '1.5l' -> (1500.0, 'ml')
        """
        match = self.size_pattern.match(size_str)
        if not match:
            return None

        value_str, unit_str = match.groups()
        value = float(value_str)

        unit_info = self.conversion_map.get(unit_str)
        if not unit_info:
            return None # Unknown unit

        # Convert to the base unit
        base_unit = unit_info['base']
        canonical_value = value * unit_info['multiplier']
        
        return (canonical_value, base_unit)

    def get_canonical_sizes(self, product) -> set:
        """
        Takes a Product object and returns a set of its canonical size tuples.
        e.g., { (500.0, 'g'), (6.0, 'pk') }
        """
        # We need to instantiate the normalizer to get the standardized sizes
        normalizer = ProductNormalizer(product.__dict__)
        standardized_sizes = normalizer.standardized_sizes
        
        canonical_sizes = set()
        if not standardized_sizes:
            return canonical_sizes

        for size_str in standardized_sizes:
            parsed_size = self._parse_size(size_str)
            if parsed_size:
                canonical_sizes.add(parsed_size)
        
        return canonical_sizes
