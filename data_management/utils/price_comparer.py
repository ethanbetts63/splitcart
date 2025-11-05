from datetime import timedelta
from django.utils import timezone
from products.models import Price

class PriceComparer:
    """
    A utility class to compare the price lists of two stores.
    """
    def __init__(self, freshness_days=3, overlap_threshold=0.98):
        self.freshness_threshold = timezone.now() - timedelta(days=freshness_days)
        self.overlap_threshold = overlap_threshold

    def compare(self, store_a, store_b):
        """
        Compares two stores based on the 'True Overlap' of their current prices.

        Returns:
            bool: True if the stores are a match, False otherwise.
        """
        # 1. Fetch current prices for both stores
        prices_a = Price.objects.filter(
            store=store_a,
            scraped_date__gte=self.freshness_threshold
        ).values('product_id', 'price')

        prices_b = Price.objects.filter(
            store=store_b,
            scraped_date__gte=self.freshness_threshold
        ).values('product_id', 'price')

        # If either store has no current prices, they cannot be compared.
        if not prices_a.exists() or not prices_b.exists():
            return False

        # 2. Create price dictionaries for efficient lookup
        price_map_a = {p['product_id']: p['price'] for p in prices_a}
        price_map_b = {p['product_id']: p['price'] for p in prices_b}

        # 3. Find the set of common products
        common_product_ids = set(price_map_a.keys()) & set(price_map_b.keys())

        if not common_product_ids:
            return False # No common products to compare

        # 4. Count matching prices for common products
        match_count = 0
        for product_id in common_product_ids:
            if price_map_a[product_id] == price_map_b[product_id]:
                match_count += 1

        # 5. Calculate True Overlap and compare against the threshold
        true_overlap = match_count / len(common_product_ids)

        return true_overlap >= self.overlap_threshold
