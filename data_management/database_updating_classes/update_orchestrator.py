import os
import json
from products.models import Product
from companies.models import Company, Store
from django.core.cache import cache
from data_management.database_updating_classes.product_resolver import ProductResolver
from data_management.database_updating_classes.unit_of_work import UnitOfWork
from data_management.database_updating_classes.variation_manager import VariationManager
from data_management.database_updating_classes.brand_manager import BrandManager
from data_management.database_updating_classes.post_processor import PostProcessor
from data_management.database_updating_classes.product_enricher import ProductEnricher
from data_management.database_updating_classes.group_maintenance_orchestrator import GroupMaintenanceOrchestrator

class UpdateOrchestrator:
    def __init__(self, command, inbox_path):
        self.command = command
        self.inbox_path = inbox_path
        self.processed_files = []
        self.variation_manager = VariationManager(self.command, unit_of_work=None)

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Product Update --"))
        
        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
        # Instantiate resolver once before the loop.
        product_resolver = ProductResolver(self.command)

        unit_of_work = None # Initialize to handle cases with no processable files
        for file_path in all_files:
            self.command.stdout.write(f"{self.command.style.WARNING('--- Processing file:')} {os.path.basename(file_path)} ---")
            
            consolidated_data = self._consolidate_from_file(file_path)
            if not consolidated_data:
                self.processed_files.append(file_path)
                continue

            first_product_data = next(iter(consolidated_data.values()))
            company_name = first_product_data['metadata'].get('company')
            store_id = first_product_data['metadata'].get('store_id')

            if not company_name or not store_id:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Missing company or store_id in metadata."))
                self.processed_files.append(file_path)
                continue

            try:
                company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
                store_obj = Store.objects.get(store_id=store_id, company=company_obj)

            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store with ID {store_id} for company {company_name} not found in database."))
                self.processed_files.append(file_path)
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Error fetching company/store: {e}"))
                self.processed_files.append(file_path)
                continue


            # 1. Determine if this is a 'Full Sync' or 'Upsert Only' run
            db_price_count = Price.objects.filter(store=store_obj).count()
            file_price_count = len(consolidated_data)
            is_full_sync = False

            if db_price_count > 0:
                if (file_price_count / db_price_count) >= 0.9:
                    is_full_sync = True
            else:
                # If no prices in DB, any new file is considered a full sync
                is_full_sync = True

            # 2. Pre-fetch all existing prices for the store (for upsert and diff)
            initial_price_cache = list(Price.objects.filter(store=store_obj))

            unit_of_work = UnitOfWork(self.command, product_resolver)
            self.variation_manager.unit_of_work = unit_of_work  # Inject UoW
            brand_manager = BrandManager(self.command)

            # Pass the single resolver instance down
            product_cache = self._process_consolidated_data(consolidated_data, product_resolver, unit_of_work, self.variation_manager, brand_manager, store_obj)
            
            brand_manager.commit()

            # 3. Commit changes and get back stale prices
            stale_prices = unit_of_work.commit(consolidated_data, product_cache, product_resolver, store_obj, initial_price_cache, is_full_sync)

            if stale_prices is not None:
                self.command.stdout.write("  - Updating resolver cache with new products...")
                for norm_string, product_obj in product_cache.items():
                    if norm_string not in product_resolver.normalized_string_cache:
                        product_resolver.normalized_string_cache[norm_string] = product_obj
                        if product_obj.barcode and product_obj.barcode not in product_resolver.barcode_cache:
                            product_resolver.barcode_cache[product_obj.barcode] = product_obj

                self.processed_files.append(file_path)

                # 4. Conditionally delete stale prices
                if is_full_sync and stale_prices:
                    stale_price_ids = [p.id for p in stale_prices]
                    Price.objects.filter(id__in=stale_price_ids).delete()
                    self.command.stdout.write(self.command.style.SUCCESS(f"  - Deleted {len(stale_price_ids)} delisted products for store {store_obj.store_name}."))

                # Get the scraped_date from the metadata of the first product in the consolidated data
                # Assuming all products in a single .jsonl file share the same scrape date
                first_product_data = next(iter(consolidated_data.values()))
                scraped_date_value = first_product_data['metadata'].get('scraped_date')

                if scraped_date_value:
                    # Assign directly, assuming it's a format Django's DateTimeField can handle
                    store_obj.last_scraped = scraped_date_value
                    store_obj.save(update_fields=['last_scraped'])
                    self.command.stdout.write(self.command.style.SUCCESS(f"  - Updated last_scraped for Store PK {store_obj.pk} ({store_obj.store_name}) to {scraped_date_value}."))
                else:
                    self.command.stderr.write(self.command.style.ERROR(f"  - Warning: No 'scraped_date' found in metadata for file {os.path.basename(file_path)}. last_scraped not updated."))
            else:
                self.command.stderr.write(self.command.style.ERROR(f"  - Commit failed for file {os.path.basename(file_path)}."))