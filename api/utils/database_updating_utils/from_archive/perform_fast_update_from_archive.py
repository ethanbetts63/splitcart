import os
from django.db import transaction
from .consolidate_product_data import consolidate_product_data
from .batch_create_new_products import batch_create_new_products
from .batch_create_prices import batch_create_prices
from .batch_create_category_relationships import batch_create_category_relationships

@transaction.atomic
def perform_fast_update_from_archive(command):
    """
    Main runner function to perform the full, optimized database update.
    """
    archive_dir = os.path.join('api', 'data', 'archive', 'store_data')
    
    # Step 1: Consolidate all data from JSON files into memory
    consolidated_data = consolidate_product_data(archive_dir)
    if not consolidated_data:
        command.stdout.write(command.style.WARNING("No data consolidated. Aborting."))
        return

    # Step 2: Batch create new products and get a full product cache
    product_cache = batch_create_new_products(consolidated_data)

    # Step 3: Batch create all new price records
    batch_create_prices(consolidated_data, product_cache)

    # Step 4: Batch create all category and product-category relationships
    batch_create_category_relationships(consolidated_data, product_cache)

    command.stdout.write(command.style.SUCCESS("Fast update from archive complete."))
