import re
from data_management.utils.product_normalizer import ProductNormalizer

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

    def are_sizes_compatible(self, product_a, product_b, tolerance=0.1) -> bool:
        """
        Compares two products to see if they have at least one pair of compatible sizes.
        Compatibility is defined as having the same base unit and a value within a certain tolerance.
        This is intended for finding 'similar' but not identical sizes (Lvl 2).
        """
        sizes_a = self.get_canonical_sizes(product_a)
        sizes_b = self.get_canonical_sizes(product_b)

        if not sizes_a or not sizes_b:
            return False

        for val_a, unit_a in sizes_a:
            for val_b, unit_b in sizes_b:
                # Must have the same base unit to be comparable
                if unit_a == unit_b:
                    # For pack sizes, require an exact match
                    if unit_a == 'pk':
                        if val_a == val_b:
                            return True
                    # For other units, check if they are within the tolerance
                    else:
                        if abs(val_a - val_b) <= (val_a * tolerance):
                            return True
        
        return False

    def are_sizes_different(self, product_a, product_b) -> bool:
        """
        Compares two products and returns True if their canonical size sets are different.
        This is a simple check for inequality, suitable for Lvl 1 and Lvl 4.
        """
        sizes_a = self.get_canonical_sizes(product_a)
        sizes_b = self.get_canonical_sizes(product_b)

        if not sizes_a or not sizes_b:
            return False

        return sizes_a != sizes_b
