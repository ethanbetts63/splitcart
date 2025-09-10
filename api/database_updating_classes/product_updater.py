import os
import json
from collections import defaultdict
from .product_resolver import ProductResolver
from .unit_of_work import UnitOfWork
from companies.models import Company, Store
from products.models import Product

class ProductUpdater:
    """
    Updates products and prices from the store archive files.
    """

    def __init__(self, command, archive_path):
        self.command = command
        self.archive_path = archive_path

    def run(self):
        """
        The main public method that orchestrates the update process.
        """
        consolidated_data = self._consolidate_data()
        if not consolidated_data:
            self.command.stdout.write(self.command.style.WARNING("No data consolidated. Aborting."))
            return

        self._process_data(consolidated_data)

    def _consolidate_data(self):
        """
        Consolidates product data from all store archive files.
        """
        self.command.stdout.write("--- Consolidating product data from JSON files ---")
        consolidated_data = defaultdict(list)

        if not os.path.exists(self.archive_path):
            self.command.stdout.write(self.command.style.WARNING(f"Archive directory not found: {self.archive_path}"))
            return {}

        for company_folder in os.scandir(self.archive_path):
            if not company_folder.is_dir():
                continue
            for store_file in os.scandir(company_folder.path):
                if not store_file.name.endswith('.json'):
                    continue
                
                with open(store_file.path, 'r') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                store_id = metadata.get('store_id')
                if not store_id:
                    continue

                for product_data in data.get('products', []):
                    consolidated_data[store_id].append(product_data)
        
        self.command.stdout.write(f"Consolidated data for {len(consolidated_data)} stores.")
        return consolidated_data

    def _process_data(self, consolidated_data):
        """
        Processes the consolidated data, one store at a time.
        """
        for store_id, products in consolidated_data.items():
            self.command.stdout.write(f"--- Processing store: {store_id} ---")
            try:
                store_obj = Store.objects.select_related('company').get(store_id=store_id)
            except Store.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Store with ID {store_id} not found in database."))
                continue

            resolver = ProductResolver(self.command, store_obj.company, store_obj)
            unit_of_work = UnitOfWork(self.command)

            store_consolidated_data = self._consolidate_store_data(products)

            product_cache = self._identify_products(store_consolidated_data, resolver, unit_of_work, store_obj)

            unit_of_work.commit(store_consolidated_data, product_cache, resolver, store_obj)

    def _consolidate_store_data(self, products):
        """
        Consolidates product data for a single store.
        """
        consolidated_data = {}
        for product_data in products:
            key = product_data.get('normalized_name_brand_size')
            if not key:
                continue
            if key in consolidated_data:
                continue
            # Get the most recent price from the history
            if product_data.get('price_history'):
                most_recent_price = sorted(product_data['price_history'], key=lambda x: x['scraped_at'], reverse=True)[0]
                product_data['price_current'] = most_recent_price.get('price')
                product_data['product_id_store'] = most_recent_price.get('sku')
                # Extract the date part from the ISO format timestamp
                product_data['scraped_date'] = most_recent_price.get('scraped_at', '').split('T')[0]
            consolidated_data[key] = {'product': product_data, 'metadata': {'company': ''}} 
        return consolidated_data

    def _identify_products(self, consolidated_data, resolver, unit_of_work, store_obj):
        """
        Identifies existing and new products for a single store.
        """
        product_cache = {}
        for key, data in consolidated_data.items():
            product_details = data['product']
            existing_product = resolver.find_match(product_details, [])

            if existing_product:
                product_cache[key] = existing_product
                new_normalized_name = product_details.get('normalized_name')
                if new_normalized_name and new_normalized_name not in existing_product.name_variations:
                    existing_product.name_variations.append(new_normalized_name)
                    unit_of_work.add_for_update(existing_product)
                unit_of_work.add_price(existing_product, store_obj, product_details)
            else:
                new_product = Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand'),
                    barcode=product_details.get('barcode'),
                    normalized_name_brand_size=key,
                    name_variations=[product_details.get('normalized_name')],
                    size=product_details.get('sizes', [])[0] if product_details.get('sizes') else None,
                    sizes=product_details.get('sizes', []),
                    url=product_details.get('price_history', [{}])[0].get('url'),
                    image_url=product_details.get('image_url'),
                    description=product_details.get('description'),
                    country_of_origin=product_details.get('country_of_origin'),
                    ingredients=product_details.get('ingredients')
                )
                product_cache[key] = new_product
                unit_of_work.add_new_product(new_product, product_details)
        return product_cache