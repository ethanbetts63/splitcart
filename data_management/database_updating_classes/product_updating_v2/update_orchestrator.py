import os
from datetime import datetime
from django.utils import timezone
from django.db.models import Max
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
        
        all_brands = ProductBrand.objects.all()
        self.caches['normalized_brand_names'] = {b.normalized_name: b for b in all_brands}
        self.command.stdout.write(f"  - Cached {len(self.caches['normalized_brand_names'])} brands by normalized name.")

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

        self.caches['prices_by_store'] = {}
        self.command.stdout.write("  - Initialized empty container for price caches.")

    def _prepare_price_cache_for_store(self, store):
        """Builds a lightweight, two-level price cache for a specific store."""
        self.command.stdout.write(f"    - Preparing price cache for store: {store.store_name} ({store.store_id})")
        price_data = Price.objects.filter(store=store).values('price_hash', 'pk', 'product_id')
        
        hash_to_pk_cache = {p['price_hash']: p['pk'] for p in price_data if p['price_hash']}
        product_id_to_pk_cache = {p['product_id']: p['pk'] for p in price_data}

        self.caches['prices_by_store'][store.id] = {
            'hash_to_pk': hash_to_pk_cache,
            'product_id_to_pk': product_id_to_pk_cache
        }
        self.command.stdout.write(f"      - Cached {len(hash_to_pk_cache)} price hashes for store.")

    def _is_file_valid(self, metadata, raw_product_data):
        """Performs all validation checks on a file before processing."""
        if not metadata or not raw_product_data:
            self.command.stdout.write("  - File is empty or metadata is missing, skipping.")
            return False, None

        try:
            store = Store.objects.get(store_id=metadata['store_id'])
        except Store.DoesNotExist:
            self.command.stderr.write(self.command.style.ERROR(f"  - Store with ID {metadata['store_id']} not found in database. Skipping file."))
            return False, None

        # 1. Scrape date must be newer than the latest price date in DB for this store
        incoming_scraped_date_str = metadata.get('scraped_date')
        if not incoming_scraped_date_str:
            self.command.stderr.write(self.command.style.ERROR("  - 'scraped_date' not found in metadata. Skipping file."))
            return False, None
        
        try:
            incoming_scraped_date = datetime.fromisoformat(incoming_scraped_date_str)
            if timezone.is_naive(incoming_scraped_date):
                incoming_scraped_date = timezone.make_aware(incoming_scraped_date)
        except (ValueError, TypeError):
            self.command.stderr.write(self.command.style.ERROR(f"  - Could not parse 'scraped_date': {incoming_scraped_date_str}. Skipping file."))
            return False, None

        latest_db_scraped_date = Price.objects.filter(store=store).aggregate(Max('scraped_date'))['scraped_date__max']

        if latest_db_scraped_date and incoming_scraped_date.date() <= latest_db_scraped_date:
            self.command.stdout.write(self.command.style.WARNING(
                f"  - Stale file: Its date ({incoming_scraped_date.date()}) is not newer than the latest DB price date ({latest_db_scraped_date}). Skipping."
            ))
            return False, None

        # 2. Product count must be at least 90% of the DB count (full sync check)
        db_price_count = Price.objects.filter(store=store).count()
        file_product_count = len(raw_product_data)
        
        if db_price_count > 0 and (file_product_count / db_price_count) < 0.9:
            self.command.stderr.write(self.command.style.ERROR(
                f"  - Partial scrape detected for {store.store_name} (file count: {file_product_count} vs. DB count: {db_price_count}). Skipping file to prevent data loss."
            ))
            return False, None
        
        return True, store

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

            is_valid, store_or_reason = self._is_file_valid(metadata, raw_product_data)
            if not is_valid:
                continue
            
            store = store_or_reason

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
