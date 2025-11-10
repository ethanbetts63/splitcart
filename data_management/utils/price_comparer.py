class PriceComparer:
    """
    A utility class to compare the price lists of two stores.
    This class is designed to work with pre-fetched price data for performance.
    """
    def __init__(self, overlap_threshold=0.98):
        self.overlap_threshold = overlap_threshold

    def compare(self, price_map_a: dict, price_map_b: dict):
        """
        Compares two stores based on the 'True Overlap' of their current prices.

        Args:
            price_map_a: A dictionary of {product_id: price} for store A.
            price_map_b: A dictionary of {product_id: price} for store B.

        Returns:
            bool: True if the stores are a match, False otherwise.
        """
        # If either store has no prices, they cannot be compared.
        if not price_map_a or not price_map_b:
            return False

        # 1. Find the set of common products
        common_product_ids = set(price_map_a.keys()) & set(price_map_b.keys())

        if not common_product_ids:
            return False # No common products to compare

        # 2. Count matching prices for common products
        match_count = 0
        for product_id in common_product_ids:
            if price_map_a[product_id] == price_map_b[product_id]:
                match_count += 1

        # 3. Calculate True Overlap and compare against the threshold
        true_overlap = match_count / len(common_product_ids)

        return true_overlap >= self.overlap_threshold
