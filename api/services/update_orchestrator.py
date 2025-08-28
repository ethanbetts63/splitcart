import os
import json
from datetime import datetime
from products.models import Product, Price
from .product_resolver import ProductResolver
from .unit_of_work import UnitOfWork
from .variation_manager import VariationManager
from .translation_table_generator import TranslationTableGenerator

class UpdateOrchestrator:
    def __init__(self, command, inbox_path):
        self.command = command
        self.inbox_path = inbox_path
        self.unit_of_work = UnitOfWork(command)
        self.resolver = ProductResolver(command)
        self.variation_manager = VariationManager(command, self.unit_of_work)
        self.translator_generator = TranslationTableGenerator(command)
        self.processed_files = []

    def run(self):
        self.command.stdout.write(self.command.style.SQL_FIELD("--- Starting OOP Refactored Product Update ---"))
        
        all_files = [os.path.join(root, file) for root, _, files in os.walk(self.inbox_path) for file in files if file.endswith('.jsonl')]
        
        for file_path in all_files:
            self.command.stdout.write(f"--- Processing file: {os.path.basename(file_path)} ---")
            consolidated_data = self._consolidate_from_file(file_path)
            if not consolidated_data:
                self.processed_files.append(file_path)
                continue

            product_cache = self._process_consolidated_data(consolidated_data)
            
            if self.unit_of_work.commit(consolidated_data, product_cache, self.resolver):
                self.processed_files.append(file_path)

        self.variation_manager.commit_hotlist()
        self.variation_manager.reconcile_duplicates()
        self.translator_generator.generate()
        self._cleanup_processed_files()

        self.command.stdout.write(self.command.style.SUCCESS("--- Orchestrator finished ---"))

    def _consolidate_from_file(self, file_path):
        consolidated_data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.command.stdout.write(f"  - Consolidating {len(lines)} raw product entries...")
            for line in lines:
                try:
                    data = json.loads(line)
                    product_data = data.get('product')
                    metadata = data.get('metadata')
                    if not product_data or not metadata:
                        continue

                    key = product_data.get('normalized_name_brand_size')
                    if not key:
                        continue
                    
                    if key not in consolidated_data:
                        consolidated_data[key] = {
                            'product_details': product_data,
                            'metadata': metadata,
                            'price_history': []
                        }
                    
                    price_entry = {
                        'store_id': metadata.get('store_id'),
                        'price': product_data.get('price_current'),
                        'date': metadata.get('scraped_at')
                    }
                    consolidated_data[key]['price_history'].append(price_entry)
                except json.JSONDecodeError:
                    continue
        self.command.stdout.write(f"  - Consolidated into {len(consolidated_data)} unique products.")
        return consolidated_data

    def _process_consolidated_data(self, consolidated_data):
        product_cache = {}
        total = len(consolidated_data)
        for i, (key, data) in enumerate(consolidated_data.items()):
            self.command.stdout.write(f'\r    - Identifying products: {i+1}/{total}', ending='')
            product_details = data['product_details']
            price_history = data['price_history']
            company_name = data['metadata'].get('company', '')

            existing_product = self.resolver.find_match(product_details, price_history)

            if existing_product:
                product_cache[key] = existing_product
                self.variation_manager.check_for_variation(product_details, existing_product, company_name)
                self._add_prices_to_unit_of_work(existing_product, product_details, price_history)
            else:
                new_product = Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand'),
                    barcode=product_details.get('barcode'),
                    normalized_name_brand_size=product_details.get('normalized_name_brand_size')
                )
                product_cache[key] = new_product
                self.unit_of_work.add_new_product(new_product)
                self._add_prices_to_unit_of_work(new_product, product_details, price_history)
        self.command.stdout.write('\n')
        return product_cache

    def _add_prices_to_unit_of_work(self, product, product_details, price_history):
        for price in price_history:
            store_obj = self.resolver.store_cache.get(price['store_id'])
            if not store_obj:
                continue

            # Check against the cache to prevent creating duplicate prices
            try:
                scraped_date = datetime.fromisoformat(price['date']).date()
                price_key = (product.id, store_obj.id, scraped_date)

                if price_key not in self.resolver.price_cache:
                    self.unit_of_work.add_new_price(Price(product=product, store=store_obj, price=price['price'], store_product_id=product_details.get('product_id_store')))
                    # Add the new price to the cache to prevent duplicates within the same run
                    self.resolver.price_cache.add(price_key)
            except (ValueError, TypeError):
                # Handle cases where the date format is invalid
                continue

    def _cleanup_processed_files(self):
        self.command.stdout.write("--- Cleaning up processed inbox files ---")
        for file_path in self.processed_files:
            try:
                os.remove(file_path)
                self.command.stdout.write(f"  - Removed {os.path.basename(file_path)}")
            except OSError as e:
                self.command.stderr.write(self.command.style.ERROR(f'Could not remove file {file_path}: {e}'))
