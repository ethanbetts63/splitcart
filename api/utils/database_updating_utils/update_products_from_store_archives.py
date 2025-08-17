
import os
import json
import logging
from tqdm import tqdm
from django.db import transaction
from companies.models import Store
from .get_or_create_product import get_or_create_product
from .create_price import create_price

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_products_from_store_archives(command):
    """
    Updates products and prices from store-specific JSON archives.
    """
    archive_dir = os.path.join('api', 'data', 'archive', 'store_data')
    if not os.path.exists(archive_dir):
        command.stdout.write(command.style.WARNING(f"Archive directory not found: {archive_dir}"))
        return

    company_folders = [f for f in os.scandir(archive_dir) if f.is_dir()]
    for company_folder in tqdm(company_folders, desc="Processing companies"):
        command.stdout.write(command.style.SUCCESS(f"Processing company: {company_folder.name}"))
        store_files = [f for f in os.scandir(company_folder.path) if f.name.endswith('.json')]
        
        for store_file in tqdm(store_files, desc=f"Updating products for {company_folder.name}", leave=False):
            with open(store_file.path, 'r') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            store_id = metadata.get('store_id')
            if not store_id:
                logger.warning(f"Skipping file {store_file.name}, missing store_id in metadata.")
                continue

            try:
                store = Store.objects.get(id=store_id)
            except Store.DoesNotExist:
                logger.warning(f"Store with id {store_id} not found. Skipping.")
                continue

            products = data.get('products', [])
            with transaction.atomic():
                for product_data in products:
                    product_obj = get_or_create_product(product_data, command)
                    if not product_obj:
                        continue

                    for price_data in product_data.get('price_history', []):
                        create_price(product_obj, store, price_data, command)
