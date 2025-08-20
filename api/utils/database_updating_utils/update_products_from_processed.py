import os
import json
from django.db import transaction
from django.conf import settings
from datetime import datetime
from companies.models import Company
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

from api.utils.database_updating_utils.from_archive.batch_create_new_products import batch_create_new_products
from api.utils.database_updating_utils.from_archive.batch_create_prices import batch_create_prices
from api.utils.database_updating_utils.from_archive.batch_create_category_relationships import batch_create_category_relationships

def update_products_from_processed(command):
    processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')

    if not os.path.exists(processed_data_path):
        command.stdout.write(command.style.WARNING('Processed data directory not found.'))
        return

    for filename in os.listdir(processed_data_path):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(processed_data_path, filename)
        command.stdout.write(command.style.SQL_FIELD(f'--- Processing file: {filename} ---'))

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data.get('metadata', {})
        products = data.get('products', [])

        if not all([metadata, products]):
            command.stdout.write(command.style.WARNING(f'Skipping {filename}: missing metadata or products key.'))
            continue

        # Step 1: Consolidate data into the format expected by the batch functions.
        # The key is used for the lookup cache that is passed between steps.
        consolidated_data = {}
        for p in products:
            name = str(p.get('name', ''))
            brand = str(p.get('brand', ''))
            size = str(p.get('package_size', ''))
            # This key is for local caching between steps, not for database lookups.
            key = (name.strip().lower(), brand.strip().lower(), size.strip().lower())

            price_info = {
                'store_id': metadata.get('store_id'),
                'price': p.get('price_current'),
                'is_on_special': p.get('is_on_sale', False),
                'is_available': True,
                'store_product_id': p.get('store_product_id') # Pass this along
            }

            consolidated_data[key] = {
                'product_details': p,
                'price_history': [price_info],
                'category_paths': [p.get('category_path', [])],
                'company_name': metadata.get('company')
            }

        try:
            with transaction.atomic():
                # Step 2: Identify products and create new ones using tiered matching.
                product_cache = batch_create_new_products(command, consolidated_data)

                # Step 3: Batch create all new price records.
                batch_create_prices(command, consolidated_data, product_cache)

                # Step 4: Batch create all category and product-category relationships.
                batch_create_category_relationships(consolidated_data, product_cache)

            os.remove(file_path)
            command.stdout.write(command.style.SUCCESS(f'  Successfully processed and removed {filename}.'))

        except Exception as e:
            command.stderr.write(command.style.ERROR(f'  An error occurred processing {filename}. The file will not be deleted. Error: {e}'))

    command.stdout.write(command.style.SUCCESS("\n--- Product update from processed data complete ---"))