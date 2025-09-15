from api.utils.substitution_utils.size_comparer import SizeComparer

class UnitPriceSorter:
    """
    A utility to sort product-price pairs by their calculated unit price.
    """

    def __init__(self):
        self.size_comparer = SizeComparer()

    def _calculate_unit_price(self, product, price):
        """
        Calculates the unit price for a single product-price pair.
        Returns the unit price and the canonical size string, or (None, None) if not calculable.
        """
        canonical_sizes = self.size_comparer.get_canonical_sizes(product)

        # We can only calculate unit price if there's one unambiguous canonical size.
        if len(canonical_sizes) != 1:
            return None, None

        canonical_value, base_unit = list(canonical_sizes)[0]

        if canonical_value is None or canonical_value == 0:
            return None, None

        unit_price = float(price.price) / canonical_value
        canonical_size_str = f"{canonical_value}{base_unit}"
        
        return unit_price, canonical_size_str

    def sort_by_unit_price(self, product_price_pairs: list) -> list:
        """
        Sorts a list of (Product, Price) tuples by their unit price in ascending order.

        Args:
            product_price_pairs: A list of tuples, where each tuple contains a
                                 Product object and its corresponding Price object.

        Returns:
            A sorted list of dictionaries, each containing the product, price,
            calculated unit price, and canonical size string. Products that
            could not be sorted are excluded.
        """
        sortable_products = []
        for product, price in product_price_pairs:
            unit_price, canonical_size = self._calculate_unit_price(product, price)
            if unit_price is not None:
                sortable_products.append({
                    'product': product,
                    'price': price,
                    'unit_price': unit_price,
                    'canonical_size': canonical_size
                })

        # Sort the list of dictionaries by the 'unit_price' key
        return sorted(sortable_products, key=lambda x: x['unit_price'])
