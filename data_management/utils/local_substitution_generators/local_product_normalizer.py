import re

class LocalProductNormalizer:
    def __init__(self, product_data, brand_cache=None):
        self.name = str(product_data.get('name', ''))
        self.brand = str(product_data.get('brand')) if product_data.get('brand') else ''
        self.size = str(product_data.get('size', ''))
        self.raw_sizes = self._extract_all_sizes()
        self.standardized_sizes = self._get_standardized_sizes()

    def _extract_all_sizes(self) -> list:
        all_sizes = set()
        for text in [self.name, self.brand, self.size]:
            if not text: continue
            sizes = self._extract_sizes_from_string(text)
            for size in sizes:
                all_sizes.add(size.lower())
        return sorted(list(all_sizes))

    def _extract_sizes_from_string(self, text: str) -> list:
        sizes = set()
        # This is a simplified version of the original complex regex for portability.
        # It captures patterns like '500g', '1.5l', '6pk'.
        pattern = r'(\d+\.?\d*)\s*(g|kg|ml|l|pk|pack|each|ea)\b'
        for match in re.finditer(pattern, text.lower()):
            value, unit = match.groups()
            unit = unit.replace('pack', 'pk').replace('each', 'ea')
            sizes.add(f"{value}{unit}")
        return list(sizes)

    def _get_standardized_sizes(self) -> list:
        from .local_size_comparer import LocalSizeComparer
        size_comparer = LocalSizeComparer()
        canonical_sizes = {}
        for size_str in self.raw_sizes:
            s = size_str.lower().replace(" ", "").replace("pack", "pk").replace("each", "ea")
            if s == '1ea': s = 'ea'
            parsed_tuple = size_comparer._parse_size(s)
            if parsed_tuple:
                if parsed_tuple not in canonical_sizes:
                    value, unit = parsed_tuple
                    canonical_sizes[parsed_tuple] = f"{int(value) if value.is_integer() else value}{unit}"
            else:
                if s not in canonical_sizes.values():
                    canonical_sizes[('str', s)] = s
        return sorted(list(canonical_sizes.values()))