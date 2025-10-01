import os
import json
from products.models import Product
from companies.models import Company, Store
from django.core.cache import cache
from data_management.database_updating_classes.product_resolver import ProductResolver
from data_management.database_updating_classes.unit_of_work import UnitOfWork
from data_management.database_updating_classes.variation_manager import VariationManager
from data_management.database_updating_classes.product_translation_table_generator import ProductTranslationTableGenerator
from data_management.database_updating_classes.brand_translation_table_generator import BrandTranslationTableGenerator
from data_management.database_updating_classes.brand_manager import BrandManager
from data_management.database_updating_classes.product_reconciler import ProductReconciler
from data_management.database_updating_classes.brand_reconciler import BrandReconciler
from data_management.database_updating_classes.category_cycle_manager import CategoryCycleManager
from data_management.database_updating_classes.group_orchestrator import GroupOrchestrator

class UpdateOrchestrator:
    def __init__(self, command, inbox_path):
        self.command = command
        self.inbox_path = inbox_path
        self.processed_files = []
        self.variation_manager = VariationManager(self.command, unit_of_work=None)

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Product Update --"))
        
        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
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

                # Stamp the store as a candidate for its group, if it belongs to one.
                if hasattr(store_obj, 'group_membership') and store_obj.group_membership:
                    group = store_obj.group_membership.group
                    group.candidates.add(store_obj)

            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store with ID {store_id} for company {company_name} not found in database."))
                self.processed_files.append(file_path)
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Error fetching company/store: {e}"))
                self.processed_files.append(file_path)
                continue

            resolver = ProductResolver(self.command, company_obj, store_obj)
            unit_of_work = UnitOfWork(self.command, resolver)
            self.variation_manager.unit_of_work = unit_of_work  # Inject UoW
            brand_manager = BrandManager(self.command)

            product_cache = self._process_consolidated_data(consolidated_data, resolver, unit_of_work, self.variation_manager, brand_manager, store_obj)
            
            brand_manager.commit()

            if unit_of_work.commit(consolidated_data, product_cache, resolver, store_obj):
                self.processed_files.append(file_path)

                # Get the scraped_date from the metadata of the first product in the consolidated data
                # Assuming all products in a single .jsonl file share the same scrape date
                first_product_data = next(iter(consolidated_data.values()))
                scraped_date_value = first_product_data['metadata'].get('scraped_date')

                if scraped_date_value:
                    # Assign directly, assuming it's a format Django's DateTimeField can handle
                    store_obj.last_scraped = scraped_date_value
                    store_obj.save()
                    self.command.stdout.write(self.command.style.SUCCESS(f"  - Updated last_scraped for Store PK {store_obj.pk} ({store_obj.store_name}) to {scraped_date_value}."))
                    cache.delete(f"scraping_lock_{store_obj.pk}") # Clear the lock
                else:
                    self.command.stderr.write(self.command.style.ERROR(f"  - Warning: No 'scraped_date' found in metadata for file {os.path.basename(file_path)}. last_scraped not updated."))

        # After processing all files, run post-processing if a UoW was created
        if unit_of_work:
            # Run the group orchestrator to infer prices
            self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Group Orchestration --"))
            group_orchestrator = GroupOrchestrator(unit_of_work)
            group_orchestrator.run()

            # Regenerate the translation tables to include new variations
            BrandTranslationTableGenerator().run()
            ProductTranslationTableGenerator().run()

            # Run the product reconciler to merge duplicates based on the translation table
            product_reconciler = ProductReconciler(self.command)
            product_reconciler.run()

            # Run the brand reconciler to merge duplicates based on the translation table
            brand_reconciler = BrandReconciler(self.command)
            brand_reconciler.run()

            # Run category cycle pruning as a final cleanup step
            self.command.stdout.write(self.command.style.SUCCESS("--- Running Category Cycle Pruning ---"))
            all_companies = Company.objects.all()
            if not all_companies.exists():
                self.command.stdout.write(self.command.style.WARNING("No companies found, skipping cycle pruning."))
            else:
                for company in all_companies:
                    manager = CategoryCycleManager(self.command, company)
                    manager.prune_cycles()

        # Final cleanup of processed files
        self._cleanup_processed_files()

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

            existing_product = resolver.find_match(product_details, [])

            if existing_product:
                product_cache[key] = existing_product
                variation_manager.check_for_variation(product_details, existing_product, company_name)

                # --- Enrich existing product ---
                updated = False

                # Merge sizes lists
                incoming_sizes = set(product_details.get('sizes', []))
                if incoming_sizes:
                    existing_sizes = set(existing_product.sizes)
                    if not incoming_sizes.issubset(existing_sizes):
                        combined_sizes = sorted(list(existing_sizes.union(incoming_sizes)))
                        existing_product.sizes = combined_sizes
                        updated = True

                if not existing_product.barcode and product_details.get('barcode'):
                    existing_product.barcode = product_details.get('barcode')
                    updated = True
                if not existing_product.url and product_details.get('url'):
                    existing_product.url = product_details.get('url')
                    updated = True
                if not existing_product.image_url and product_details.get('image_url_main'):
                    existing_product.image_url = product_details.get('image_url_main')
                    updated = True
                new_description = product_details.get('description_long') or product_details.get('description_short')
                if new_description:
                    if not existing_product.description or len(new_description) < len(existing_product.description):
                        existing_product.description = new_description
                        updated = True
                if not existing_product.country_of_origin and product_details.get('country_of_origin'):
                    existing_product.country_of_origin = product_details.get('country_of_origin')
                    updated = True
                if not existing_product.ingredients and product_details.get('ingredients'):
                    existing_product.ingredients = product_details.get('ingredients')
                    updated = True
                
                # Update name_variations
                new_normalized_name = product_details.get('normalized_name')
                if new_normalized_name and new_normalized_name not in existing_product.name_variations:
                    existing_product.name_variations.append(new_normalized_name)
                    updated = True

                if company_name.lower() == 'coles' and not product_details.get('barcode') and not existing_product.has_no_coles_barcode:
                    existing_product.has_no_coles_barcode = True
                    updated = True

                # Update brand_name_company_pairs
                raw_brand_name = product_details.get('brand')
                new_pair = [raw_brand_name, company_name]
                
                found_existing_company_pair = False
                if existing_product.brand_name_company_pairs:
                    for i, pair in enumerate(existing_product.brand_name_company_pairs):
                        if pair[1] == company_name: # Check if company already exists in a pair
                            found_existing_company_pair = True
                            if pair[0] != raw_brand_name: # If brand name is different, do nothing (user rule)
                                pass
                            else: # Same brand name, no change needed
                                pass
                            break
                
                if not found_existing_company_pair:
                    if not existing_product.brand_name_company_pairs:
                        existing_product.brand_name_company_pairs = []
                    existing_product.brand_name_company_pairs.append(new_pair)
                    updated = True

                if updated:
                    unit_of_work.add_for_update(existing_product)
                
                unit_of_work.add_price(existing_product, store_obj, product_details)
            else:
                normalized_brand_key = product_details.get('normalized_brand')
                brand_obj = brand_manager.brand_cache.get(normalized_brand_key)
                new_product = Product(
                    name=product_details.get('name', ''),
                    normalized_name=product_details.get('normalized_name'),
                    name_variations=[product_details.get('normalized_name')],
                    brand=brand_obj,
                    brand_name_company_pairs=[[product_details.get('brand'), company_name]],
                    barcode=product_details.get('barcode'),
                    normalized_name_brand_size=key,
                    size=product_details.get('size'),
                    sizes=product_details.get('sizes', []),
                    url=product_details.get('url'),
                    image_url=product_details.get('image_url_main'),
                    description=(product_details.get('description_long') or product_details.get('description_short')),
                    country_of_origin=product_details.get('country_of_origin'),
                    ingredients=product_details.get('ingredients')
                )
                if company_name.lower() == 'coles' and not product_details.get('barcode'):
                    new_product.has_no_coles_barcode = True

                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product, product_details)
        self.command.stdout.write('\n')
        return product_cache

    def _cleanup_processed_files(self):
        self.command.stdout.write("--- Moving processed inbox files to temp storage ---")
        temp_storage_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'temp_product_storage')
        
        os.makedirs(temp_storage_path, exist_ok=True)

        for file_path in self.processed_files:
            try:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(temp_storage_path, file_name)
                os.rename(file_path, destination_path)
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not move file {file_path}: {e}'))