import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from datetime import datetime

# Define constants for failed products
FAILED_PRODUCTS_DIR = os.path.join(settings.BASE_DIR, 'api', 'data', 'failed_products')
from api.utils.database_updating_utils.get_or_create_product import get_or_create_product
from api.utils.database_updating_utils.create_price import create_price
from api.utils.database_updating_utils.get_or_create_category_hierarchy import get_or_create_category_hierarchy
from api.utils.database_updating_utils.get_or_create_company import get_or_create_company
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

def update_products_from_processed(command):
    processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')
    failed_products_data = {} # Initialize failed products data

    if not os.path.exists(processed_data_path):
        command.stdout.write(command.style.WARNING('Processed data directory not found.'))
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
            command.stdout.write(command.style.WARNING(f'Skipping {filename}: missing metadata or products key.'))
            continue

        company_name = metadata.get('company')
        if not company_name:
            command.stdout.write(command.style.WARNING(f'Skipping {filename}: missing company in metadata.'))
            continue

        company_obj, company_created = get_or_create_company(company_name)
        store_id = metadata.get('store_id')
        if not store_id:
            command.stdout.write(command.style.WARNING(f'Skipping {filename}: missing store_id in metadata.'))
            continue

        store_obj, created = get_or_create_store(
            company_obj=company_obj,
            division_obj=None,
            store_id=store_id,
            store_data=metadata
        )

        if not store_obj:
            command.stdout.write(command.style.ERROR(f'Could not get or create store from metadata in {filename}. Skipping.'))
            continue

        display_store_name = store_obj.name if store_obj.name != 'N/A' else store_obj.store_id
        command.stdout.write(command.style.SQL_FIELD(f'--- Processing file: {filename} for store: {display_store_name} ---'))

        try:
            with transaction.atomic():
                products_created = 0
                products_updated = 0
                products_failed = 0
                for product_data in products:
                    category_path = product_data.get('category_path', [])
                    if not category_path:
                        products_failed += 1
                        company_entry = failed_products_data.setdefault(company_name, {})
                        store_entry = company_entry.setdefault(store_id, [])
                        store_entry.append({
                            'product_data': product_data,
                            'reason': 'missing category_path'
                        })
                        continue

                    category_obj = get_or_create_category_hierarchy(category_path, company_obj)
                    product_obj, created = get_or_create_product(product_data, store_obj, category_obj)
                    product_obj.category.add(category_obj)
                    
                    create_price(product_data, product_obj, store_obj)
                    if created:
                        products_created += 1
                    else:
                        products_updated += 1
            
            os.remove(file_path)
            command.stdout.write(command.style.SUCCESS(f'  Successfully processed products for {filename}. Created: {products_created}, Updated: {products_updated}, Failed: {products_failed}'))

        except Exception as e:
            command.stderr.write(command.style.ERROR(f'  An error occurred processing {filename}. The file will not be deleted. Error: {e}'))

    if failed_products_data:
        os.makedirs(FAILED_PRODUCTS_DIR, exist_ok=True)
        today_str = datetime.now().strftime('%Y-%m-%d')
        failed_file_path = os.path.join(FAILED_PRODUCTS_DIR, f'failed_products_{today_str}.json')
        
        with open(failed_file_path, 'w', encoding='utf-8') as f:
            json.dump(failed_products_data, f, indent=4)
        command.stdout.write(command.style.SQL_FIELD(f'Saved failed products to: {failed_file_path}'))

    command.stdout.write(command.style.SUCCESS("\n--- Product update from processed data complete ---"))
