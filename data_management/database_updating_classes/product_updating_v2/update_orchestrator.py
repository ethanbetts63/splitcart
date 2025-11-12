import os
from django.conf import settings
from products.models import Product, ProductBrand
from .file_reader import FileReader
from .brand_manager import BrandManager
from .product_manager import ProductManager

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
        
        # We will also need a SKU cache, which is more complex as it's per-company
        self.caches['products_by_sku'] = {}
        for p in all_products:
            if p.company_skus:
                for company, skus in p.company_skus.items():
                    if company not in self.caches['products_by_sku']:
                        self.caches['products_by_sku'][company] = {}
                    for sku in skus:
                        self.caches['products_by_sku'][company][sku] = p
        self.command.stdout.write(f"  - Cached products for {len(self.caches['products_by_sku'])} companies by SKU.")


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

        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
        for file_path in all_files:
            self.command.stdout.write(f"\n{self.command.style.WARNING('--- Processing file:')} {os.path.basename(file_path)} ---")
            
            file_reader = FileReader(file_path)
            # Note: read_and_consolidate needs to be implemented in FileReader
            raw_product_data = file_reader.read_and_consolidate()

            if not raw_product_data:
                self.command.stdout.write("  - File is empty or invalid, skipping.")
                # Optionally delete empty/invalid file
                # os.remove(file_path)
                continue

            # 1. Process Brands
            brand_manager.process(raw_product_data)

            # 2. Process Products
            product_manager.process(raw_product_data)

            # 3. Process Prices (Future)
            # price_manager.process(raw_product_data)

            # 4. Cleanup
            # os.remove(file_path)
            self.command.stdout.write(f"  - Finished processing file: {os.path.basename(file_path)}")

        self.command.stdout.write(self.command.style.SUCCESS("-- Orchestrator finished --"))
