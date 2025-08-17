
import os
import json
import sys
from django.db import transaction
from companies.models import Store
from .get_or_create_product import get_or_create_product
from .create_price import create_price
from .get_or_create_category_hierarchy import get_or_create_category_hierarchy

def update_products_from_store_archives(command):
    """
    Updates products and prices from store-specific JSON archives.
    """
    archive_dir = os.path.join('api', 'data', 'archive', 'store_data')
    if not os.path.exists(archive_dir):
        command.stdout.write(command.style.WARNING(f"Archive directory not found: {archive_dir}"))
        return

    products_updated = 0
    products_created = 0
    product_count = 0

    company_folders = [f for f in os.scandir(archive_dir) if f.is_dir()]
    for company_folder in company_folders:
        command.stdout.write(command.style.SUCCESS(f"Processing company: {company_folder.name}"))
        store_files = [f for f in os.scandir(company_folder.path) if f.name.endswith('.json')]
        
        for store_file in store_files:
            with open(store_file.path, 'r') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            store_id = metadata.get('store_id')
            if not store_id:
                continue

            try:
                store = Store.objects.get(store_id=store_id)
            except Store.DoesNotExist:
                continue

            products = data.get('products', [])
            with transaction.atomic():
                for product_data in products:
                    product_count += 1
                    category_paths = product_data.get('category_paths', [])
                    if not category_paths:
                        continue
                    
                    category_path = category_paths[0]
                    category_obj = get_or_create_category_hierarchy(category_path, store.company)

                    product_obj, created = get_or_create_product(product_data, store, category_obj)
                    
                    if created:
                        products_created += 1
                    else:
                        products_updated += 1
                    
                    if product_count % 100 == 0:
                        command.stdout.write(f"    Products: updated {products_updated}, created {products_created}")

                    if not product_obj:
                        continue

                    for price_data in product_data.get('price_history', []):
                        create_price(price_data, product_obj, store)
    
    command.stdout.write(f"    Total Products: updated {products_updated}, created {products_created}")
    command.stdout.write("\n")
    
    
