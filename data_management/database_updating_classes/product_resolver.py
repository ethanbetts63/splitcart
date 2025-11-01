from products.models import Product, Price
from companies.models import Store

class ProductResolver:
    """
    Handles all logic related to matching incoming products with existing database records.
    It builds and holds caches of database state to provide fast, in-memory lookups.
    A single instance is created per run, with global caches built once.
    The context for a specific store (for SKU and price caches) is set as needed.
    """
    def __init__(self, command):
        """
        Initializes the resolver and builds the global, run-level caches.
        """
        self.command = command
        self._build_global_caches()
        # Initialize contextual caches to empty dicts
        self.sku_cache = {}
        self.price_cache = {}

    def _build_global_caches(self):
        """
        Builds the in-memory caches for data that is consistent across all stores.
        This is done only once per run.
        """
        self.command.stdout.write("--- Building Global Caches ---")
        
        # All products (not filtered by company/store, as barcode/normalized_string are global)
        all_products = list(Product.objects.all())
        
        # Cache 1: Barcode (Highest Priority)
        self.barcode_cache = {p.barcode: p for p in all_products if p.barcode}
        self.command.stdout.write(f"  - Built cache for {len(self.barcode_cache)} barcodes.")

        # Cache 3: Normalized Name-Brand-Size String (Fallback)
        self.normalized_string_cache = {p.normalized_name_brand_size: p for p in all_products if p.normalized_name_brand_size}
        self.command.stdout.write(f"  - Built cache for {len(self.normalized_string_cache)} normalized strings.")

        # Cache 4: Stores (still global, as we need to resolve any store_id to an object)
        self.store_cache = {s.store_id: s for s in Store.objects.all()}
        self.command.stdout.write(f"  - Built cache for {len(self.store_cache)} stores.")

    def set_context(self, current_store_obj):
        """
        Sets the store-specific context by building caches for SKU and prices for that store.
        """
        self.command.stdout.write(f"--- Building Contextual Caches for {current_store_obj.name} ---")
        self._build_contextual_caches(current_store_obj)

    def _build_contextual_caches(self, current_store_obj):
        """
        Builds caches for data that is specific to the given store.
        """
        # Filter prices by the current store for relevant caches to prevent SKU conflicts.
        relevant_prices_query = Price.objects.select_related('price_record', 'price_record__product').filter(
            store=current_store_obj
        )

        relevant_prices = list(relevant_prices_query.all())
        # Cache 2: SKU (contextual)
        self.sku_cache = {}
        prices_with_ids = [p for p in relevant_prices if p.sku and p.price_record and p.price_record.product]
        for price in prices_with_ids:
            # Key is just the sku, as the cache is already filtered by company/store
            self.sku_cache[price.sku] = price.price_record.product
        self.command.stdout.write(f"  - Built cache for {len(self.sku_cache)} contextual SKUs.")

        # Cache 5: Existing Prices (contextual)
        self.price_cache = {p.normalized_key for p in relevant_prices if p.normalized_key}
        self.command.stdout.write(f"  - Built cache for {len(self.price_cache)} contextual existing prices.")

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

        # Tier 2: Match by SKU (contextual lookup)
        if not product:
            sku = product_details.get('sku')
            if sku and sku in self.sku_cache:
                product = self.sku_cache[sku]
                return product

        # Tier 3: Match by Normalized String
        if not product:
            normalized_string = product_details.get('normalized_name_brand_size')
            if normalized_string in self.normalized_string_cache:
                product = self.normalized_string_cache[normalized_string]
                return product
        
        return None

    def add_new_product_to_cache(self, product):
        """
        Updates the global caches with a new product that is about to be created.
        This is used for de-duplication within a single run.
        """
        if product.barcode:
            self.barcode_cache[product.barcode] = product
        if product.normalized_name_brand_size:
            self.normalized_string_cache[product.normalized_name_brand_size] = product
        # sku cache is not updated here as it's handled by the UnitOfWork's price creation
