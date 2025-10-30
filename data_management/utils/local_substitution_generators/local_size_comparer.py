import re

class LocalSizeComparer:
    def __init__(self):
        self.conversion_map = {
            'g':  {'base': 'g',  'multiplier': 1.0},
            'kg': {'base': 'g',  'multiplier': 1000.0},
            'ml': {'base': 'ml', 'multiplier': 1.0},
            'l':  {'base': 'ml', 'multiplier': 1000.0},
            'pk': {'base': 'pk', 'multiplier': 1.0},
            'ea': {'base': 'ea', 'multiplier': 1.0},
        }
        self.size_pattern = re.compile(r"(\d+\.?\d*)\s*([a-z]+)$")

    def _parse_size(self, size_str: str) -> tuple | None:
        match = self.size_pattern.match(size_str)
        if not match: return None
        value_str, unit_str = match.groups()
        value = float(value_str)
        unit_info = self.conversion_map.get(unit_str)
        if not unit_info: return None
        return (value * unit_info['multiplier'], unit_info['base'])

    def get_canonical_sizes(self, product_dict) -> set:
        from .local_product_normalizer import LocalProductNormalizer
        normalizer = LocalProductNormalizer(product_dict)
        canonical_sizes = set()
        for size_str in normalizer.standardized_sizes:
            parsed_size = self._parse_size(size_str)
            if parsed_size: canonical_sizes.add(parsed_size)
        return canonical_sizes

    def are_sizes_compatible(self, prod_a, prod_b, tolerance=0.1) -> bool:
        sizes_a = self.get_canonical_sizes(prod_a)
        sizes_b = self.get_canonical_sizes(prod_b)
        if not sizes_a or not sizes_b: return False
        for val_a, unit_a in sizes_a:
            for val_b, unit_b in sizes_b:
                if unit_a == unit_b:
                    if unit_a == 'pk':
                        if val_a == val_b: return True
                    else:
                        if abs(val_a - val_b) <= (val_a * tolerance): return True
        return False