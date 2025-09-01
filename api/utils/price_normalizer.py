
class PriceNormalizer:
    """
    A utility class to generate a normalized key for a price record.
    """

    @staticmethod
    def get_normalized_key(product_id: int, store_id: int, price: float, date: str) -> str:
        """
        Generates a normalized key for a price record.

        Args:
            product_id: The ID of the product.
            store_id: The ID of the store.
            price: The price of the product.
            date: The date of the price, in ISO format (YYYY-MM-DD).

        Returns:
            A normalized key string.
        """
        return f"{product_id}-{store_id}-{price}-{date}"
