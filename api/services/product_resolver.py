from products.models import Product, Price
from companies.models import Store

class ProductResolver:
    """
    Handles all logic related to matching incoming products with existing database records.
    It builds and holds caches of database state to provide fast, in-memory lookups.
    """
    def __init__(self, command):
        self.command = command
        self._build_caches()

    def _build_caches(self):
        """
        Builds the in-memory caches for products, prices, and stores.
        """
        self.command.stdout.write("--- Building resolver caches ---")
        
        all_products = list(Product.objects.all())
        
        # Cache 1: Barcode (Highest Priority)
        self.barcode_cache = {p.barcode: p for p in all_products if p.barcode}
        self.command.stdout.write(f"  - Built cache for {len(self.barcode_cache)} barcodes.")

        # Cache 2: Store-Specific Product ID
        self.store_product_id_cache = {}
        all_prices = Price.objects.select_related('product', 'store').all()
        prices_with_ids = [p for p in all_prices if p.store_product_id]
        for price in prices_with_ids:
            key = (price.store.store_id, price.store_product_id)
            self.store_product_id_cache[key] = price.product
        self.command.stdout.write(f"  - Built cache for {len(self.store_product_id_cache)} store-specific product IDs.")

        # Cache 3: Normalized Name-Brand-Size String (Fallback)
        self.normalized_string_cache = {p.normalized_name_brand_size: p for p in all_products if p.normalized_name_brand_size}
        self.command.stdout.write(f"  - Built cache for {len(self.normalized_string_cache)} normalized strings.")

        # Cache 4: Stores
        self.store_cache = {s.store_id: s for s in Store.objects.all()}
        self.command.stdout.write(f"  - Built cache for {len(self.store_cache)} stores.")

        # Cache 5: Existing Prices
        self.price_cache = {(p.product_id, p.store_id, p.scraped_at.date()) for p in all_prices}
        self.command.stdout.write(f"  - Built cache for {len(self.price_cache)} existing prices.")

        self.command.stdout.write("--- Caches built successfully ---")

    def find_match(self, product_details, price_history):
        """
        Implements the 3-tier matching logic to find an existing product.

        Args:
            product_details (dict): The consolidated details of the incoming product.
            price_history (list): The price history, used to get store_id for Tier 2.

        Returns:
            Product: An existing Product object if a match is found, otherwise None.
        """
        product = None
        
        # Tier 1: Match by Barcode
        barcode = product_details.get('barcode')
        if barcode and barcode in self.barcode_cache:
            product = self.barcode_cache[barcode]
            return product

        # Tier 2: Match by Store Product ID
        if not product:
            # Use the first price entry to get the store_id for this product
            if price_history:
                store_id = price_history[0].get('store_id')
                store_product_id = product_details.get('product_id_store') # Corrected key
                if store_id and store_product_id and (store_id, store_product_id) in self.store_product_id_cache:
                    product = self.store_product_id_cache[(store_id, store_product_id)]
                    return product

        # Tier 3: Match by Normalized String
        if not product:
            normalized_string = product_details.get('normalized_name_brand_size')
            if normalized_string in self.normalized_string_cache:
                product = self.normalized_string_cache[normalized_string]
                return product
        
        return None

    def add_new_product_to_cache(self, product):
        """Updates the caches with a new product that is about to be created."""
        if product.barcode:
            self.barcode_cache[product.barcode] = product
        if product.normalized_name_brand_size:
            self.normalized_string_cache[product.normalized_name_brand_size] = product