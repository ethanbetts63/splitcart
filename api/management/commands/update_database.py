import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from datetime import datetime

# Define constants for failed products
FAILED_PRODUCTS_DIR = os.path.join(settings.BASE_DIR, 'api', 'data', 'failed_products')
from api.utils.database_updating_utils import (
    get_or_create_product,
    create_price,
    get_or_create_category_hierarchy,
    get_or_create_company,
    get_or_create_store,
    TallyCounter
)

class Command(BaseCommand):
    help = 'Updates the database with the latest processed data.'

    def handle(self, *args, **options):
        processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')
        self.failed_products_data = {} # Initialize failed products data
        tally_counter = TallyCounter()

        if not os.path.exists(processed_data_path):
            self.stdout.write(self.style.WARNING('Processed data directory not found.'))
            return

        for filename in os.listdir(processed_data_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(processed_data_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            products = data.get('products', [])

            if not all([metadata, products]):
                self.stdout.write(self.style.WARNING(f'Skipping {filename}: missing metadata or products key.'))
                continue

            company_name = metadata.get('company')
            if not company_name:
                self.stdout.write(self.style.WARNING(f'Skipping {filename}: missing company in metadata.'))
                continue

            company_obj, company_created = get_or_create_company(company_name)
            store_id = metadata.get('store_id')
            if not store_id:
                self.stdout.write(self.style.WARNING(f'Skipping {filename}: missing store_id in metadata.'))
                continue

            store_obj, created = get_or_create_store(
                company_obj=company_obj,
                division_obj=None,
                store_id=store_id,
                store_data=metadata
            )

            if not store_obj:
                self.stdout.write(self.style.ERROR(f'Could not get or create store from metadata in {filename}. Skipping.'))
                continue

            self.stdout.write(self.style.SUCCESS(f'--- Processing file: {filename} for store: {store_obj.name} ---'))

            try:
                with transaction.atomic():
                    product_count = 0
                    for product_data in products:
                        category_path = product_data.get('category_path', [])
                        if not category_path:
                            self.stdout.write(self.style.WARNING(f"    - Product '{product_data.get('name')}' is missing category_path. Saving to failed products."))
                            company_entry = self.failed_products_data.setdefault(company_name, {})
                            store_entry = company_entry.setdefault(store_id, [])
                            store_entry.append({
                                'product_data': product_data,
                                'reason': 'missing category_path'
                            })
                            continue

                        category_obj = get_or_create_category_hierarchy(category_path, company_obj)
                        product_obj = get_or_create_product(product_data, company_obj.name, tally_counter)
                        product_obj.category.add(category_obj)
                        
                        create_price(product_obj, store_obj, product_data)
                        product_count += 1
                
                os.remove(file_path)
                self.stdout.write(self.style.SUCCESS(f'  Successfully processed {product_count} products and deleted {filename}'))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'  An error occurred processing {filename}. The file will not be deleted. Error: {e}'))

        if self.failed_products_data:
            os.makedirs(FAILED_PRODUCTS_DIR, exist_ok=True)
            today_str = datetime.now().strftime('%Y-%m-%d')
            failed_file_path = os.path.join(FAILED_PRODUCTS_DIR, f'failed_products_{today_str}.json')
            
            with open(failed_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_products_data, f, indent=4)
            self.stdout.write(self.style.WARNING(f'\nSaved failed products to: {failed_file_path}'))

        self.stdout.write(self.style.SUCCESS("\n--- Database update complete ---"))
