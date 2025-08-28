from products.models import Product, Price
from companies.models import Store

class ProductResolver:
    """
    Handles all logic related to matching incoming products with existing database records.
    It builds and holds caches of database state to provide fast, in-memory lookups.
    """
    def __init__(self, command, current_company_obj, current_store_obj):
        self.command = command
        self.current_company_obj = current_company_obj
        self.current_store_obj = current_store_obj
        self._build_caches(current_company_obj, current_store_obj)

    def _build_caches(self, current_company_obj, current_store_obj):
        """
        Builds the in-memory caches for products, prices, and stores, filtered by current context.
        """
        self.command.stdout.write("--- Building resolver caches (contextual) ---")
        
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

        # Filter prices by current company (and store for IGA) for relevant caches
        relevant_prices_query = Price.objects.select_related('product', 'store').filter(
            store__company=current_company_obj
        )
        if current_company_obj.name.lower() == 'iga':
            relevant_prices_query = relevant_prices_query.filter(store=current_store_obj)
        
        relevant_prices = list(relevant_prices_query.all())

        # Cache 2: Store-Specific Product ID (contextual)
        self.store_product_id_cache = {}
        prices_with_ids = [p for p in relevant_prices if p.store_product_id]
        for price in prices_with_ids:
            # Key is just the store_product_id, as the cache is already filtered by company/store
            self.store_product_id_cache[price.store_product_id] = price.product
        self.command.stdout.write(f"  - Built cache for {len(self.store_product_id_cache)} contextual store-specific product IDs.")

        # Cache 5: Existing Prices (contextual)
        self.price_cache = {(p.product_id, p.store_id, p.scraped_at.date()) for p in relevant_prices}
        self.command.stdout.write(f"  - Built cache for {len(self.price_cache)} contextual existing prices.")

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

        # Tier 2: Match by Store Product ID (contextual lookup)
        if not product:
            store_product_id = product_details.get('product_id_store')
            if store_product_id and store_product_id in self.store_product_id_cache:
                product = self.store_product_id_cache[store_product_id]
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
        Updates the caches with a new product that is about to be created.
        This is used for de-duplication within a single file's processing.
        """
        if product.barcode:
            self.barcode_cache[product.barcode] = product
        if product.normalized_name_brand_size:
            self.normalized_string_cache[product.normalized_name_brand_size] = product
        # store_product_id cache is not updated here as it's handled by the UnitOfWork's price creation
