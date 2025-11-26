import os
from datetime import datetime
from django.utils import timezone
from django.db.models import Max
from django.conf import settings
from products.models import Product, ProductBrand, Price
from companies.models import Store, Category, Company
from products.models import SKU
from .file_reader import FileReader
from .brand_manager import BrandManager
from .product_manager import ProductManager
from .price_manager import PriceManager
from .category_manager import CategoryManager
from .translation_table_generators.brand_translation_table_generator import BrandTranslationTableGenerator
from .translation_table_generators.product_translation_table_generator import ProductTranslationTableGenerator
from .post_processing.brand_reconciler import BrandReconciler
from .post_processing.product_reconciler import ProductReconciler
from .post_processing.category_cycle_manager import CategoryCycleManager
from .post_processing.orphan_product_cleaner import OrphanProductCleaner
from .group_maintanance.group_maintenance_orchestrator import GroupMaintenanceOrchestrator

class UpdateOrchestrator:
    """
    The main entry point for the V2 product update process.
    Initializes the global caches and orchestrates the pipeline for each file.
    """
    def __init__(self, command, relaxed_staleness=False):
        self.command = command
        self.relaxed_staleness = relaxed_staleness
        self.inbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'inboxes', 'product_inbox')
        self.caches = {}
        self.brand_translation_cache = {}
        self.discovered_brand_pairs = set()

        # Initialize managers
        self.brand_manager = BrandManager(self.command, self.caches, self.update_cache, self.brand_translation_cache)
        self.product_manager = ProductManager(self.command, self.caches, self.update_cache, self.discovered_brand_pairs)
        self.price_manager = PriceManager(self.command, self.caches, self.update_cache)
        self.category_manager = CategoryManager(self.command, self.caches, self.update_cache)

    def _build_global_caches(self):
        """
        Builds the initial, memory-efficient, two-tier in-memory caches.
        - Tier 1 (Lean Global Cache): Maps barcodes, norm_strings, and SKUs to product IDs (int).
        - Tier 2 (ID-to-Data Cache): Maps a product ID to a slim dictionary of essential data needed for resolution.
        """
        self.command.stdout.write("--- Building Global Caches (Lean) ---")
        
        # Brand Cache (remains as full objects, as it's not a memory bottleneck)
        all_brands = ProductBrand.objects.all()
        self.caches['normalized_brand_names'] = {b.normalized_name: b for b in all_brands}
        self.command.stdout.write(f"  - Cached {len(self.caches['normalized_brand_names'])} brands by normalized brand name.")

        # Product Caches (Lean Implementation)
        self.caches['products_by_id'] = {}
        self.caches['products_by_barcode'] = {}
        self.caches['products_by_norm_string'] = {}

        product_values = Product.objects.select_related('brand').values(
            'id', 'barcode', 'normalized_name_brand_size', 'brand__normalized_name'
        )

        for p_dict in product_values:
            product_id = p_dict['id']
            # Tier 2 cache: ID -> slim data dictionary
            self.caches['products_by_id'][product_id] = {
                'id': product_id,
                'normalized_name_brand_size': p_dict['normalized_name_brand_size'],
                'brand_normalized_name': p_dict['brand__normalized_name']
            }
            # Tier 1 caches: key -> ID
            if p_dict['barcode']:
                self.caches['products_by_barcode'][p_dict['barcode']] = product_id
            if p_dict['normalized_name_brand_size']:
                self.caches['products_by_norm_string'][p_dict['normalized_name_brand_size']] = product_id

        self.command.stdout.write(f"  - Cached {len(self.caches['products_by_id'])} products by ID (lean).")
        self.command.stdout.write(f"  - Cached {len(self.caches['products_by_barcode'])} products by barcode.")
        self.command.stdout.write(f"  - Cached {len(self.caches['products_by_norm_string'])} products by normalized name-brand-size string.")
        
        # SKU Cache - Will be loaded Just-in-Time for each company
        self.caches['products_by_sku'] = {}
        self.command.stdout.write("  - Initialized empty container for SKU cache (will be loaded JIT).")

        # Category Cache (Company-Aware, no change needed)
        all_categories = Category.objects.select_related('company').all()
        self.caches['categories'] = {(c.name, c.company_id): c for c in all_categories}
        self.command.stdout.write(f"  - Cached {len(self.caches['categories'])} categories.")

        # Price Cache Container
        self.caches['prices_by_store'] = {}
        self.command.stdout.write("  - Initialized empty container for price caches.")

    def _prepare_sku_cache_for_company(self, company):
        """Builds a SKU cache for a single company, clearing any previous data."""
        self.command.stdout.write(f"--- Building SKU Cache for {company.name} ---")
        
        # Clear the old SKU cache
        self.caches['products_by_sku'].clear()

        # Fetch and cache SKUs only for the specified company
        all_skus = SKU.objects.filter(company=company).values('company__name', 'sku', 'product_id')
        
        company_sku_cache = {}
        for sku_dict in all_skus:
            company_name = sku_dict['company__name']
            if company_name not in self.caches['products_by_sku']:
                self.caches['products_by_sku'][company_name] = {}
            self.caches['products_by_sku'][company_name][sku_dict['sku']] = sku_dict['product_id']
        
        self.command.stdout.write(f"  - Cached {len(all_skus)} product IDs by SKU for {company.name}.")

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

    def _deduplicate_product_data_for_pricing(self, raw_product_data: list) -> list:
        self.command.stdout.write("  - De-duplicating product list for PriceManager...")
        final_list_for_pricing = []
        seen_product_ids = set()

        for data in raw_product_data:
            product_dict = data.get('product', {})
            if not product_dict:
                continue

            # Resolve the canonical product ID using the cache, which now contains aliases
            nnbs = product_dict.get('normalized_name_brand_size')
            canonical_product_id = self.caches['products_by_norm_string'].get(nnbs)

            if not canonical_product_id:
                # This can happen if the product was new and couldn't be resolved by barcode/sku.
                # The nnbs is its own canonical key. We use the nnbs itself to track uniqueness
                # for products that are new in this run and haven't been assigned a PK yet.
                if nnbs not in seen_product_ids:
                     final_list_for_pricing.append(data)
                     seen_product_ids.add(nnbs)
                continue

            # If we found a canonical product, use its ID for uniqueness check
            if canonical_product_id not in seen_product_ids:
                final_list_for_pricing.append(data)
                seen_product_ids.add(canonical_product_id)
        
        self.command.stdout.write(f"  - Original list size: {len(raw_product_data)}, De-duplicated list size: {len(final_list_for_pricing)}")
        return final_list_for_pricing

    def run(self):
        """The main orchestration method."""
        self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Product Update (V2) --"))
        
        self._build_global_caches()

        all_files = sorted([os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')])
        
        current_company_id_in_cache = None

        for file_path in all_files:
            self.command.stdout.write(f"\n{self.command.style.WARNING('--- Processing file:')} {os.path.basename(file_path)} ---")
            
            # Clear the discovered pairs cache for each new file
            self.discovered_brand_pairs.clear()

            file_reader = FileReader(file_path)
            metadata, raw_product_data = file_reader.read_and_consolidate()

            is_valid, store_or_reason = self._is_file_valid(metadata, raw_product_data)
            if not is_valid:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass  # File is already gone, which is fine.
                continue
            
            store = store_or_reason

            # JIT Caching for SKUs
            if store.company.id != current_company_id_in_cache:
                self._prepare_sku_cache_for_company(store.company)
                current_company_id_in_cache = store.company.id

            # 1. Process Products (runs first to discover brand pairs)
            self.product_manager.process(raw_product_data, store.company)

            # 1.5. De-duplicate the product list before pricing to prevent unique constraint errors
            final_list_for_pricing = self._deduplicate_product_data_for_pricing(raw_product_data)
            
            # 2. Process Brands
            self.brand_manager.process(raw_product_data, self.discovered_brand_pairs)

            # 3. Prepare Price Cache for the current store
            self._prepare_price_cache_for_store(store)

            # 4. Process Prices
            self.price_manager.process(final_list_for_pricing, store)

            # 5. Process Categories
            self.category_manager.process(raw_product_data, store.company)

            # 6. Cleanup
            try:
                os.remove(file_path)
                self.command.stdout.write(f"  - Successfully processed and deleted file: {os.path.basename(file_path)}")
            except FileNotFoundError:
                self.command.stdout.write(f"  - File already removed, skipping deletion: {os.path.basename(file_path)}")


        # --- Post-Processing Section ---
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Post-Processing Run Started ---"))
        
        # 1. First, generate translation tables based on the latest data
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Generating Translation Tables ---"))
        BrandTranslationTableGenerator().run()
        ProductTranslationTableGenerator().run()

        # 2. Reconcile Brands and Products using the new tables
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Reconciling Duplicates ---"))
        BrandReconciler(self.command).run()
        ProductReconciler(self.command).run()

        # 3. Prune Category Cycles
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Pruning Category Cycles ---"))
        for company in Company.objects.all():
            CategoryCycleManager(self.command, company).prune_cycles()

        # 4. Run Group Maintenance
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Running Group Maintenance ---"))
        GroupMaintenanceOrchestrator(self.command, relaxed_staleness=self.relaxed_staleness).run()

        # 5. Regenerate Translation Tables after reconciliation
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Generating Translation Tables ---"))
        BrandTranslationTableGenerator().run()
        ProductTranslationTableGenerator().run()

        # 6. Final Cleanup: Remove products with no prices
        self.command.stdout.write(self.command.style.SUCCESS("\n--- Cleaning Orphan Products ---"))
        OrphanProductCleaner(self.command).run()

        self.command.stdout.write(self.command.style.SUCCESS("\n-- Orchestrator finished --"))