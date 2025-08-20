import sys
from django.utils.text import slugify
from datetime import datetime
from django.db import close_old_connections
from companies.models import Store
from .build_product_list import build_product_list
from .save_json_file import save_json_file

def archive_single_store(store_id):
    """
    Worker function to build a JSON archive for a single store.
    Designed to be called from a multiprocessing pool.
    """
    try:
        # Each process needs its own DB connection.
        close_old_connections()

        store = Store.objects.select_related('company').get(store_id=store_id)
        
        # Iterate through the generator to show progress
        product_list = []
        products_processed_count = 0
        for product_data in build_product_list(store):
            product_list.append(product_data)
            products_processed_count += 1
            # Print progress on the same line
            sys.stdout.write(f"\r  - Processed {products_processed_count} products...")
            sys.stdout.flush()

        # Clear the progress line after the loop
        if products_processed_count > 0:
            sys.stdout.write("\r" + " " * 50 + "\r") 
            sys.stdout.flush()

        if not product_list:
            return {'status': 'skipped', 'store_name': store.store_name, 'reason': 'No products found.'}

        store_data = {
            'metadata': {
                'store_id': store.store_id,
                'store_name': store.store_name,
                'company_name': store.company.name,
                'address_line_1': store.address_line_1,
                'suburb': store.suburb,
                'state': store.state,
                'postcode': store.postcode,
                'data_generation_date': datetime.now().isoformat(),
                'total_products': len(product_list),
            },
            'products': product_list
        }

        company_slug = slugify(store.company.name)

        # Clean up the store_id to handle cases like 'COL:123'
        cleaned_store_id = store.store_id
        if ':' in cleaned_store_id:
            cleaned_store_id = cleaned_store_id.split(':')[-1]

        saved_path = save_json_file(company_slug, cleaned_store_id, store_data)
        return {'status': 'success', 'store_name': store.store_name, 'path': saved_path, 'products_found': len(product_list)}

    except Exception as e:
        # Ensure exceptions in worker processes are caught and reported
        return {'status': 'error', 'store_id': store_id, 'error': str(e)}
    finally:
        # Ensure connections are closed
        close_old_connections()

