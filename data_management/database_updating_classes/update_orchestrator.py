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
                store_obj = Store.objects.select_related('group_membership__group').get(store_id=store_id, company=company_obj)

                if not hasattr(store_obj, 'group_membership') or not store_obj.group_membership:
                    self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store {store_obj.store_name} does not belong to a group."))
                    self.processed_files.append(file_path)
                    continue
                store_group = store_obj.group_membership.group

                # Stamp the store as a candidate for its group
                store_group.candidates.add(store_obj)

            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store with ID {store_id} for company {company_name} not found in database."))
                self.processed_files.append(file_path)
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Error fetching company/store: {e}"))
                self.processed_files.append(file_path)
                continue


            unit_of_work = UnitOfWork(self.command, product_resolver)
            self.variation_manager.unit_of_work = unit_of_work  # Inject UoW
            brand_manager = BrandManager(self.command)

            # Pass the single resolver instance down
            product_cache = self._process_consolidated_data(consolidated_data, product_resolver, unit_of_work, self.variation_manager, brand_manager, store_group)
            
            brand_manager.commit()

            if unit_of_work.commit(consolidated_data, product_cache, product_resolver, store_group):
                self.command.stdout.write("  - Updating resolver cache with new products...")
                for norm_string, product_obj in product_cache.items():
                    if norm_string not in product_resolver.normalized_string_cache:
                        product_resolver.normalized_string_cache[norm_string] = product_obj
                        if product_obj.barcode and product_obj.barcode not in product_resolver.barcode_cache:
                            product_resolver.barcode_cache[product_obj.barcode] = product_obj

                self.processed_files.append(file_path)

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

        # After processing all files, run post-processing if a UoW was created
        if unit_of_work:
            post_processor = PostProcessor(self.command, unit_of_work)
            post_processor.run()

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

    def _process_consolidated_data(self, consolidated_data, resolver, unit_of_work, variation_manager, brand_manager, store_group):
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
                
                unit_of_work.add_price(existing_product, store_group, product_details, metadata)
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
                    image_url_pairs=product_details.get('image_url_pairs', []),
                )
                if company_name.lower() == 'coles' and not product_details.get('barcode'):
                    new_product.has_no_coles_barcode = True

                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product, product_details, metadata)
        self.command.stdout.write('\n')
        return product_cache

    def _cleanup_processed_files(self):
        self.command.stdout.write("--- Deleting processed inbox files ---")
        
        for file_path in self.processed_files:
            try:
                os.remove(file_path)
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not delete file {file_path}: {e}'))