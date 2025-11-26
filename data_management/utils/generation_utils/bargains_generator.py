from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from products.models import Product, Price
from companies.models import StoreGroup

class BargainsGenerator:
    """
    Identifies products with significant price variations across all anchor stores
    and sets a `has_bargain` flag on the Product model for fast sorting.
    This version fetches data directly from the database.
    """
    def __init__(self, command, dev=False):
        self.command = command
        # The 'dev' parameter is no longer used but kept for interface consistency.
        self.dev = dev

    def _fetch_anchor_store_ids(self):
        """Fetches anchor store IDs directly from the database."""
        self.command.stdout.write("  - Fetching anchor stores from database...")
        anchor_ids = list(StoreGroup.objects.filter(
            anchor__isnull=False, 
            anchor__prices__isnull=False
        ).values_list('anchor_id', flat=True).distinct())
        self.command.stdout.write(f"    - Found {len(anchor_ids)} anchor stores.")
        return anchor_ids

    def _fetch_prices_from_db(self, store_ids, threshold):
        """Fetches recent prices for given store IDs directly from the database."""
        self.command.stdout.write("  - Fetching recent prices from database...")
        # Use .values() to get a list of dictionaries, which is memory-efficient
        # and matches the format the rest of the script expects.
        prices = list(Price.objects.filter(
            store_id__in=store_ids,
            scraped_date__gte=threshold
        ).values('product_id', 'price'))
        self.command.stdout.write(f"    - Fetched {len(prices)} prices.")
        return prices

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("--- Starting Bargain Flag Generation (Direct DB) ---"))

        # Step 1: Reset all existing flags
        self.command.stdout.write("  - Resetting all `has_bargain` flags to False...")
        num_reset = Product.objects.update(has_bargain=False)
        self.command.stdout.write(f"    - Reset {num_reset} products.")

        # Step 2: Fetch anchor stores and all their prices directly from the DB
        anchor_store_ids = self._fetch_anchor_store_ids()
        if not anchor_store_ids:
            self.command.stdout.write("  - No anchor stores found. Aborting.")
            return

        freshness_threshold = timezone.now() - timedelta(days=7)
        prices = self._fetch_prices_from_db(anchor_store_ids, freshness_threshold)

        # Step 3: Process prices to find bargains
        self.command.stdout.write("  - Grouping prices by product...")
        prices_by_product = {}
        for price in prices:
            # price is already a dict {'product_id': ..., 'price': ...}
            if price['product_id'] not in prices_by_product:
                prices_by_product[price['product_id']] = []
            prices_by_product[price['product_id']].append(price)
        self.command.stdout.write(f"    - Grouped prices for {len(prices_by_product)} unique products.")

        self.command.stdout.write("  - Identifying products with bargain-level discounts...")
        product_ids_to_flag = []
        for product_id, product_prices in prices_by_product.items():
            # We need prices from at least two different stores to compare
            if len(product_prices) < 2:
                continue

            # Ensure prices are converted to Decimal for accurate comparison
            min_price = min(Decimal(p['price']) for p in product_prices)
            max_price = max(Decimal(p['price']) for p in product_prices)

            if min_price > 0 and max_price > min_price:
                discount_percentage = round(((max_price - min_price) / max_price) * 100)
                
                # New rule: Discount between 10% and 75%
                if 10 <= discount_percentage <= 75:
                    product_ids_to_flag.append(product_id)
        
        self.command.stdout.write(f"    - Found {len(product_ids_to_flag)} products to flag as bargains.")

        # Step 4: Bulk update the products that are bargains
        if product_ids_to_flag:
            self.command.stdout.write("  - Updating `has_bargain` flag in the database...")
            updated_count = Product.objects.filter(id__in=product_ids_to_flag).update(has_bargain=True)
            self.command.stdout.write(f"    - Successfully flagged {updated_count} products.")

        self.command.stdout.write(self.command.style.SUCCESS("--- Bargain Flag Generation Complete ---"))
