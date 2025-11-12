import os
from django.conf import settings
from products.models import Product, ProductBrand, Price
from companies.models import Store
from .file_reader import FileReader
from .brand_manager import BrandManager
from .product_manager import ProductManager
# from .price_manager import PriceManager # Future import

class UpdateOrchestrator:
    """
    The main entry point for the V2 product update process.
    Initializes the global caches and orchestrates the pipeline for each file.
    """
    def __init__(self, command):
        self.command = command
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'product_inbox')
        self.caches = {}

    def _build_global_caches(self):
        """Builds the initial in-memory caches for all relevant models."""
        self.command.stdout.write("--- Building Global Caches ---")
        
        # Brand Cache
        all_brands = ProductBrand.objects.all()
        self.caches['normalized_brand_names'] = {b.normalized_name: b for b in all_brands}
        self.command.stdout.write(f"  - Cached {len(self.caches['normalized_brand_names'])} brands by normalized name.")

        # Product Caches
        all_products = Product.objects.select_related('brand').all()
        self.caches['products_by_barcode'] = {p.barcode: p for p in all_products if p.barcode}
        self.caches['products_by_norm_string'] = {p.normalized_name_brand_size: p for p in all_products if p.normalized_name_brand_size}
        self.command.stdout.write(f"  - Cached {len(self.caches['products_by_barcode'])} products by barcode.")
        self.command.stdout.write(f"  - Cached {len(self.caches['products_by_norm_string'])} products by normalized string.")
        
        self.caches['products_by_sku'] = {}
        for p in all_products:
            if p.company_skus:
                for company, skus in p.company_skus.items():
                    if company not in self.caches['products_by_sku']:
                        self.caches['products_by_sku'][company] = {}
                    for sku in skus:
                        self.caches['products_by_sku'][company][sku] = p
        self.command.stdout.write(f"  - Cached products for {len(self.caches['products_by_sku'])} companies by SKU.")

        # Price Cache Container
        self.caches['prices_by_store'] = {}
        self.command.stdout.write("  - Initialized empty container for price caches.")

    def _prepare_price_cache_for_store(self, store):
        """Builds a lightweight, two-level price cache for a specific store."""
        self.command.stdout.write(f"    - Preparing price cache for store: {store.store_name} ({store.store_id})")
        
        # Use .values() for a highly efficient query
        price_data = Price.objects.filter(store=store).values('price_hash', 'pk', 'product_id')
        
        hash_to_pk_cache = {p['price_hash']: p['pk'] for p in price_data if p['price_hash']}
        product_id_to_pk_cache = {p['product_id']: p['pk'] for p in price_data}

        self.caches['prices_by_store'][store.id] = {
            'hash_to_pk': hash_to_pk_cache,
            'product_id_to_pk': product_id_to_pk_cache
        }
        self.command.stdout.write(f"      - Cached {len(hash_to_pk_cache)} price hashes for store.")

    def update_cache(self, cache_name, key, value):
        """A centralized method for managers to update the shared cache."""
        if cache_name in self.caches:
            self.caches[cache_name][key] = value

    def run(self):
        """The main orchestration method."""
        self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Product Update (V2) --"))
        
        self._build_global_caches()

        brand_manager = BrandManager(self.command, self.caches, self.update_cache)
        product_manager = ProductManager(self.command, self.caches, self.update_cache)
        # price_manager = PriceManager(self.command, self.caches, self.update_cache) # Future

        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
        for file_path in all_files:
            self.command.stdout.write(f"\n{self.command.style.WARNING('--- Processing file:')} {os.path.basename(file_path)} ---")
            
            file_reader = FileReader(file_path)
            metadata, raw_product_data = file_reader.read_and_consolidate()

            # File Validation Checks (this should be a method in FileReader in future)
            # Contains data (we can get rid of this as its covered by the other checks)
            if not metadata or not raw_product_data:
                self.command.stdout.write("  - File is empty or metadata is missing, skipping.")
                continue
            # 1. first line of meta data scrape date is newer than latest in DB 
            # 2. the number of goods in the jsonl file is at least 90% of the number in the DB for that store

            try:
                store = Store.objects.get(store_id=metadata['store_id'])
            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"  - Store with ID {metadata['store_id']} not found in database. Skipping file."))
                continue

            # 1. Process Brands
            brand_manager.process(raw_product_data)

            # 2. Process Products
            product_manager.process(raw_product_data)

            # 3. Prepare Price Cache for the current store
            self._prepare_price_cache_for_store(store)

            # 4. Process Prices (Future)
            # price_manager.process(raw_product_data, store)

            # 5. Cleanup
            # os.remove(file_path)
            self.command.stdout.write(f"  - Finished processing file: {os.path.basename(file_path)}")

        self.command.stdout.write(self.command.style.SUCCESS("-- Orchestrator finished --"))
