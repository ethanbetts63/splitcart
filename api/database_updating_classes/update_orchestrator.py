import os
import json
from products.models import Product, Price
from companies.models import Company, Store
from .product_resolver import ProductResolver
from .unit_of_work import UnitOfWork
from .variation_manager import VariationManager
from .translation_table_generator import TranslationTableGenerator

class UpdateOrchestrator:
    def __init__(self, command, inbox_path):
        self.command = command
        self.inbox_path = inbox_path
        self.processed_files = []

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("-- Starting Simplified Refactored Product Update --"))
        
        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
        for file_path in all_files:
            self.command.stdout.write(f"--- Processing file: {os.path.basename(file_path)} ---")
            
            consolidated_data = self._consolidate_from_file(file_path)
            if not consolidated_data:
                self.processed_files.append(file_path)
                continue

            # Extract company and store info from the first product in the consolidated data
            first_product_data = next(iter(consolidated_data.values()))
            company_name = first_product_data['metadata'].get('company')
            store_id = first_product_data['metadata'].get('store_id')

            if not company_name or not store_id:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Missing company or store_id in metadata."))
                self.processed_files.append(file_path)
                continue

            try:
                company_obj, _ = Company.objects.get_or_create(name__iexact=company_name, defaults={'name': company_name})
                store_obj = Store.objects.get(store_id=store_id)
            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Store with ID {store_id} not found in database."))
                self.processed_files.append(file_path)
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"Skipping file {os.path.basename(file_path)}: Error fetching company/store: {e}"))
                self.processed_files.append(file_path)
                continue

            # Services are re-instantiated for each file to keep logic simple and memory clean
            resolver = ProductResolver(self.command, company_obj, store_obj)
            unit_of_work = UnitOfWork(self.command)
            variation_manager = VariationManager(self.command, unit_of_work)

            product_cache = self._process_consolidated_data(consolidated_data, resolver, unit_of_work, variation_manager, store_obj)
            
            if unit_of_work.commit(consolidated_data, product_cache, resolver):
                self.processed_files.append(file_path)
                variation_manager.commit_hotlist() # Only commit hotlist if DB commit was successful

        # Post-run reconciliation and translation generation
        # These still need a manager, but they are run once at the end.
        # For now, we instantiate them here.
        final_variation_manager = VariationManager(self.command, None) # UoW not needed for reconciliation part
        final_variation_manager.reconcile_duplicates()
        translator_generator = TranslationTableGenerator(self.command)
        translator_generator.generate()
        self._cleanup_processed_files()

        self.command.stdout.write(self.command.style.SUCCESS("-- Orchestrator finished --"))

    def _consolidate_from_file(self, file_path):
        """Reads a file and returns a dictionary of unique products, ignoring duplicates."""
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
                    
                    # If we have seen this product before in this file, ignore the duplicate.
                    if key in consolidated_data:
                        continue
                    
                    # First time seeing this product in this file, store it.
                    consolidated_data[key] = data # Store the whole original line data

                except json.JSONDecodeError:
                    continue
        self.command.stdout.write(f"  - Consolidated into {len(consolidated_data)} unique products.")
        return consolidated_data

    def _process_consolidated_data(self, consolidated_data, resolver, unit_of_work, variation_manager, store_obj):
        product_cache = {}
        total = len(consolidated_data)
        for i, (key, data) in enumerate(consolidated_data.items()):
            self.command.stdout.write(f'\r    - Identifying products: {i+1}/{total}', ending='')
            product_details = data['product']
            metadata = data['metadata']
            company_name = metadata.get('company', '')

            # We pass an empty price history because the resolver doesn't need it for this simplified flow
            existing_product = resolver.find_match(product_details, [])

            if existing_product:
                product_cache[key] = existing_product
                variation_manager.check_for_variation(product_details, existing_product, company_name)
                unit_of_work.add_price(existing_product, store_obj, product_details)
            else:
                new_product = Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand'),
                    barcode=product_details.get('barcode'),
                    normalized_name_brand_size=key
                )
                # Temporarily attach price data to the new product instance
                new_product._price_data = product_details # Store product_details for price creation
                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product)
        self.command.stdout.write('\n')
        return product_cache

    def _cleanup_processed_files(self):
        self.command.stdout.write("--- Cleaning up processed inbox files ---")
        for file_path in self.processed_files:
            try:
                os.remove(file_path)
                self.command.stdout.write(f"  - Removed {os.path.basename(file_path)}")
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not remove file {file_path}: {e}'))