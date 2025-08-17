
import os
import json
import sys
from django.db import transaction
from companies.models import Store
from products.models import Product, Price
from .get_or_create_product import get_or_create_product
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

    # In-memory cache for stores and products
    store_cache = {str(store.store_id): store for store in Store.objects.all()}
    product_cache = { (p.name.lower() if p.name else '', p.brand.lower() if p.brand else '', p.size.lower() if p.size else ''): p for p in Product.objects.all() }
    
    # This list will hold all unsaved product objects for the entire run.
    new_products_to_create = [] 
    product_category_relations = []

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

            store = store_cache.get(store_id)
            if not store:
                continue

            products = data.get('products', [])
            prices_to_create_for_store = []
            
            for product_data in products:
                product_count += 1
                category_paths = product_data.get('category_paths', [])
                if not category_paths:
                    continue
                
                product_obj, created = None, False
                for i, category_path in enumerate(category_paths):
                    category_obj = get_or_create_category_hierarchy(category_path, store.company)
                    if i == 0: # Call get_or_create_product only on the first category path
                        product_obj, created = get_or_create_product(product_data, store, category_obj, product_cache, new_products_to_create)
                    elif product_obj and category_obj:
                        if not hasattr(product_obj, 'categories_to_add'):
                            product_obj.categories_to_add = set()
                        product_obj.categories_to_add.add(category_obj.id)
                
                if created:
                    products_created += 1
                else:
                    products_updated += 1
                
                if product_count % 100 == 0:
                    command.stdout.write(f"    Products: updated {products_updated}, created {products_created}")

                if not product_obj:
                    continue

                # Store product-category relationships to be added later
                if hasattr(product_obj, 'categories_to_add'):
                    for cat_id in product_obj.categories_to_add:
                        product_category_relations.append((product_obj, cat_id))

                for price_data in product_data.get('price_history', []):
                    price_to_use = price_data.get('price')
                    if price_to_use is None:
                        continue

                    prices_to_create_for_store.append(
                        Price(
                            product=product_obj,
                            store=store,
                            price=price_to_use,
                            is_on_special=price_data.get('is_on_special', False),
                            is_available=price_data.get('is_available', True),
                            is_active=True
                        )
                    )
            
            # --- NEW "JUST-IN-TIME" LOGIC ---
            if prices_to_create_for_store:
                # 1. Find which products for this store's prices need to be created.
                products_to_save_now = {p.product for p in prices_to_create_for_store if p.product in new_products_to_create}

                if products_to_save_now:
                    # 2. Bulk create this small batch of products.
                    with transaction.atomic():
                        Product.objects.bulk_create(list(products_to_save_now))

                    # 3. Update the global product cache with the newly saved products.
                    for product in products_to_save_now:
                        saved_product = Product.objects.get(name=product.name, brand=product.brand, size=product.size)
                        composite_key = (saved_product.name.lower(), saved_product.brand.lower(), saved_product.size.lower())
                        product_cache[composite_key] = saved_product
                        
                        # 4. Remove them from the main list to avoid creating them again later.
                        new_products_to_create.remove(product)

                # 5. Update the prices with the now-saved product objects.
                for price_obj in prices_to_create_for_store:
                    if not price_obj.product.id:
                        p = price_obj.product
                        composite_key = (p.name.lower(), p.brand.lower(), p.size.lower())
                        price_obj.product = product_cache.get(composite_key)

                # 6. Now, safely bulk create the prices for this store.
                with transaction.atomic():
                    Price.objects.bulk_create(prices_to_create_for_store)

    # Bulk create any remaining new products (those that had no prices)
    if new_products_to_create:
        with transaction.atomic():
            Product.objects.bulk_create(new_products_to_create)
        # We still need to update the cache for the category relationship step.
        for product in new_products_to_create:
            saved_product = Product.objects.get(name=product.name, brand=product.brand, size=product.size)
            composite_key = (saved_product.name.lower(), saved_product.brand.lower(), saved_product.size.lower())
            product_cache[composite_key] = saved_product

    # Add category relationships for all products
    if product_category_relations:
        with transaction.atomic():
            for product, cat_id in product_category_relations:
                if not product.id:
                    composite_key = (product.name.lower(), product.brand.lower(), product.size.lower())
                    product = product_cache.get(composite_key)
                if product:
                    product.category.add(cat_id)

    command.stdout.write(f"    Total Products: updated {products_updated}, created {products_created}")
    command.stdout.write("\n")
    
    