import os
import json
from datetime import datetime
from products.models import Product, Price
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
                os.remove(file_path)
                continue

            first_product_data = next(iter(consolidated_data.values()))
            company_name = first_product_data['metadata'].get('company')
            store_id = first_product_data['metadata'].get('store_id')

            if not company_name or not store_id:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Missing company or store_id in metadata."))
                os.remove(file_path)
                continue
            try:
                company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
                store_obj = Store.objects.get(store_id=store_id, company=company_obj)

            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store with ID {store_id} for company {company_name} not found in database."))
                os.remove(file_path)
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Error fetching company/store: {e}"))
                os.remove(file_path)
                continue


            # Check if the incoming file is stale
            incoming_scraped_date_str = first_product_data['metadata'].get('scraped_date')            
            if not incoming_scraped_date_str:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Missing 'scraped_date' in metadata."))
                os.remove(file_path)
                continue
            try:
                incoming_scraped_date = datetime.fromisoformat(incoming_scraped_date_str)
            except ValueError:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Could not parse 'scraped_date': {incoming_scraped_date_str}."))
                os.remove(file_path)
                continue

            if store_obj.last_scraped and incoming_scraped_date <= store_obj.last_scraped:
                self.command.stdout.write(self.command.style.WARNING(
                    f"Skipping file {os.path.basename(file_path)}: "
                    f"Its date ({incoming_scraped_date.date()}) is not newer than the last processed date ({store_obj.last_scraped.date()})."
                ))
                os.remove(file_path)
                continue


            # 1. Determine if this is a 'Full Sync' or 'Upsert Only' run. 
            # This protects against a partial scrape corrupting the DB.
            db_price_count = Price.objects.filter(store=store_obj).count()
            file_price_count = len(consolidated_data)
            is_full_sync = False

            if db_price_count > 0:
                if (file_price_count / db_price_count) >= 0.9:
                    is_full_sync = True
            else:
                # If no prices in DB, any new file is considered a full sync
                is_full_sync = True
            
            if not is_full_sync:
                self.command.stderr.write(self.command.style.ERROR(f"  - Partial scrape detected for {store_obj.store_name} (file count {file_price_count} vs db count {db_price_count}). Running in Upsert Only mode."))

            # 2. Pre-fetch all existing prices for the store (for upsert and diff)
            initial_price_cache = Price.objects.filter(store=store_obj).values('price_hash', 'id', 'product_id')

            unit_of_work = UnitOfWork(self.command, product_resolver)
            self.variation_manager.unit_of_work = unit_of_work  # Inject UoW
            brand_manager = BrandManager(self.command)

            # Pass the single resolver instance down
            product_cache = self._process_consolidated_data(consolidated_data, product_resolver, unit_of_work, self.variation_manager, brand_manager, store_obj)
            
            brand_manager.commit()

            # 3. Commit changes and get back stale prices
            stale_price_ids = unit_of_work.commit(consolidated_data, product_cache, product_resolver, store_obj, initial_price_cache, is_full_sync)

            if stale_price_ids is not None:
                # 4. Conditionally delete stale prices
                if is_full_sync and stale_price_ids:
                    Price.objects.filter(id__in=stale_price_ids).delete()
                    self.command.stdout.write(self.command.style.SUCCESS(f"  - Deleted {len(stale_price_ids)} delisted products for store {store_obj.store_name}."))

                self.command.stdout.write("  - Updating resolver cache with new products...")
                for norm_string, product_obj in product_cache.items():
                    if norm_string not in product_resolver.normalized_string_cache:
                        product_resolver.normalized_string_cache[norm_string] = product_obj
                        if product_obj.barcode and product_obj.barcode not in product_resolver.barcode_cache:
                            product_resolver.barcode_cache[product_obj.barcode] = product_obj



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

                try:
                    os.remove(file_path)
                    self.command.stdout.write(f"  - Successfully processed and deleted file: {os.path.basename(file_path)}")
                except OSError as e:
                    self.command.stderr.write(self.command.style.ERROR(f'Could not delete file {file_path}: {e}'))

        # After processing all files, run post-processing if a UoW was created
        if unit_of_work:
            post_processor = PostProcessor(self.command, unit_of_work)
            post_processor.run()

            # Run the new group maintenance logic
            group_maintenance_orchestrator = GroupMaintenanceOrchestrator(self.command)
            group_maintenance_orchestrator.run()


        self.command.stdout.write(self.command.style.SUCCESS("-- Orchestrator finished --"))

    def _consolidate_from_file(self, file_path):
        consolidated_data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.command.stdout.write(f"  - Consolidating {len(lines)} raw product entries...")
            for line in lines:
                try:
                    data = json.loads(line)
                    product_data = data.get('product')
                    if not product_data:
                        continue
                    
                    key = product_data.get('normalized_name_brand_size')
                    if not key:
                        continue
                    
                    if key in consolidated_data:
                        continue
                    
                    consolidated_data[key] = data

                except json.JSONDecodeError:
                    continue
        self.command.stdout.write(f"  - Consolidated into {len(consolidated_data)} unique products.")
        return consolidated_data

    def _process_consolidated_data(self, consolidated_data, resolver, unit_of_work, variation_manager, brand_manager, store_obj):
        product_cache = {}
        total = len(consolidated_data)
        for i, (key, data) in enumerate(consolidated_data.items()):
            self.command.stdout.write(f'\r    - Identifying products: {i+1}/{total}', ending='')
            product_details = data['product']
            metadata = data['metadata']
            company_name = metadata.get('company', '')

            brand_manager.process_brand(
                brand_name=product_details.get('brand'), 
                normalized_brand_name=product_details.get('normalized_brand'),
                company_name=company_name
            )

            existing_product = resolver.find_match(product_details)

            if existing_product:
                product_cache[key] = existing_product
                variation_manager.check_for_variation(product_details, existing_product, company_name)

                # --- Enrich existing product ---
                updated = ProductEnricher.enrich_from_dict(existing_product, product_details, company_name)

                if updated and existing_product.pk:
                    unit_of_work.add_for_update(existing_product)
                
                unit_of_work.add_price(existing_product, store_obj, product_details, metadata)
            else:
                normalized_brand_key = product_details.get('normalized_brand')
                brand_obj = brand_manager.brand_cache.get(normalized_brand_key)

                new_product = Product(
                    name=product_details.get('name', ''),

                    brand=brand_obj,
                    brand_name_company_pairs=[[product_details.get('brand'), company_name]],
                    barcode=product_details.get('barcode'),
                    company_skus={company_name: [product_details.get('sku')]} if product_details.get('sku') else {},
                    normalized_name_brand_size=key,
                    size=product_details.get('size'),
                    sizes=product_details.get('sizes', []),
                    url=product_details.get('url'),
                )
                if company_name.lower() == 'coles' and not product_details.get('barcode'):
                    new_product.has_no_coles_barcode = True
                if company_name.lower() == 'aldi':
                    new_product.aldi_image_url = product_details.get('aldi_image_url')

                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product, product_details, metadata)
        self.command.stdout.write('\n')
        return product_cache