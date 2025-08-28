import os
from django.db import transaction
from .batch_create_new_products import batch_create_new_products
from .batch_create_prices import batch_create_prices
from .batch_create_category_relationships import batch_create_category_relationships

def update_database_from_consolidated_data(consolidated_data, processed_files, command):
    if not consolidated_data:
        command.stdout.write(command.style.WARNING("No valid products to process after consolidation."))
        # Still remove the files that were processed, even if they yielded no valid products
        if processed_files:
            for file_path in processed_files:
                os.remove(file_path)
            command.stdout.write(command.style.SUCCESS(f'  Processed and removed {len(processed_files)} files from the inbox (contained no valid products).'))
        return

    try:
        with transaction.atomic():
            product_cache = batch_create_new_products(command, consolidated_data)
            batch_create_prices(command, consolidated_data, product_cache)
            batch_create_category_relationships(consolidated_data, product_cache)

        for file_path in processed_files:
            os.remove(file_path)
        command.stdout.write(command.style.SUCCESS(f'  Successfully processed and removed {len(processed_files)} files from the inbox.'))

    except Exception as e:
        command.stderr.write(command.style.ERROR(f'  An error occurred during the database update. Files will not be deleted. Error: {e}'))
