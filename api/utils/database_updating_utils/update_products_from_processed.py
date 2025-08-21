import os
import json
import time
from django.db import transaction
from django.conf import settings
from datetime import datetime
from companies.models import Company
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

from api.utils.database_updating_utils.batch_create_new_products import batch_create_new_products
from api.utils.database_updating_utils.batch_create_prices import batch_create_prices
from api.utils.database_updating_utils.batch_create_category_relationships import batch_create_category_relationships

def update_products_from_processed(command):
    processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')

    if not os.path.exists(processed_data_path):
        command.stdout.write(command.style.WARNING('Processed data directory not found.'))
        return

    max_loops = 3
    loop_count = 0
    while loop_count < max_loops:
        loop_count += 1
        command.stdout.write(command.style.SUCCESS(f"\n--- Starting processing loop #{loop_count}/{max_loops} ---"))

        json_files = [f for f in os.listdir(processed_data_path) if f.endswith('.json')]
        if not json_files:
            command.stdout.write(command.style.SUCCESS("No files to process. Exiting loop."))
            break

        command.stdout.write(f"Found {len(json_files)} files to process.")
        for filename in json_files:
            file_path = os.path.join(processed_data_path, filename)
            command.stdout.write(command.style.SQL_FIELD(f'--- Processing file: {filename} ---'))

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                command.stderr.write(command.style.ERROR(f'  Invalid JSON in {filename}. Skipping file.'))
                continue
            
            metadata = data.get('metadata', {})
            products = data.get('products', [])

            if not all([metadata, products]):
                command.stdout.write(command.style.WARNING(f'Skipping {filename}: missing metadata or products key.'))
                continue

            consolidated_data = {}
            for p in products:
                name = str(p.get('name', ''))
                brand = str(p.get('brand', ''))
                size = str(p.get('package_size', ''))
                key = (name.strip().lower(), brand.strip().lower(), size.strip().lower())

                price_info = {
                    'store_id': metadata.get('store_id'),
                    'price': p.get('price_current'),
                    'is_on_special': p.get('is_on_sale', False),
                    'is_available': True,
                    'store_product_id': p.get('store_product_id')
                }

                consolidated_data[key] = {
                    'product_details': p,
                    'price_history': [price_info],
                    'category_paths': [p.get('category_path', [])],
                    'company_name': metadata.get('company')
                }

            try:
                with transaction.atomic():
                    product_cache = batch_create_new_products(command, consolidated_data)
                    batch_create_prices(command, consolidated_data, product_cache)
                    batch_create_category_relationships(consolidated_data, product_cache)

                os.remove(file_path)
                command.stdout.write(command.style.SUCCESS(f'  Successfully processed and removed {filename}.'))

            except Exception as e:
                command.stderr.write(command.style.ERROR(f'  An error occurred processing {filename}. The file will not be deleted. Error: {e}'))
                # Optional: wait a moment before processing the next file if a db lock is suspected
                if "database is locked" in str(e):
                    time.sleep(1)

        # After the loop, check for remaining files
        remaining_files = [f for f in os.listdir(processed_data_path) if f.endswith('.json')]
        if not remaining_files:
            command.stdout.write(command.style.SUCCESS("\nAll files processed successfully."))
            break  # Exit while loop

    if loop_count == max_loops and [f for f in os.listdir(processed_data_path) if f.endswith('.json')]:
        command.stdout.write(command.style.WARNING("\nReached max processing loops. Some files may still remain unprocessed."))

    command.stdout.write(command.style.SUCCESS("\n--- Product update from processed data complete ---"))