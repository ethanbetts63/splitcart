from .size_parser import parse_size


class SizeComparer:
    def _parse_size(self, size_str: str) -> tuple | None:
        return parse_size(size_str)

    def get_canonical_sizes(self, product) -> set:
        """
        Takes a Product object and returns a set of its canonical size tuples.
        e.g., { (500.0, 'g'), (6.0, 'pk') }
        """
        from .product_normalizer import ProductNormalizer
        normalizer = ProductNormalizer(product.__dict__)
        canonical_sizes = set()
        for size_str in normalizer.standardized_sizes:
            parsed = parse_size(size_str)
            if parsed:
                canonical_sizes.add(parsed)
        return canonical_sizes

    def are_sizes_compatible(self, product_a, product_b, tolerance=0.1) -> bool:
        """
        Returns True if the two products have at least one pair of sizes within tolerance.
        """
        sizes_a = self.get_canonical_sizes(product_a)
        sizes_b = self.get_canonical_sizes(product_b)

        if not sizes_a or not sizes_b:
            return False

        for val_a, unit_a in sizes_a:
            for val_b, unit_b in sizes_b:
                if unit_a == unit_b:
                    if unit_a == 'pk':
                        if val_a == val_b:
                            return True
                    else:
                        if abs(val_a - val_b) <= (val_a * tolerance):
                            return True
        return False

    def are_sizes_different(self, product_a, product_b) -> bool:
        """
        Returns True if the two products have different canonical size sets.
        """
        sizes_a = self.get_canonical_sizes(product_a)
        sizes_b = self.get_canonical_sizes(product_b)

        if not sizes_a or not sizes_b:
            return False

        return sizes_a != sizes_b
