import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from api.utils.database_updating_utils import (
    deactivate_prices_for_store,
    get_or_create_product,
    create_price,
    get_or_create_category_hierarchy
)
from companies.models import Store, Company

class Command(BaseCommand):
    help = 'Updates the database with the latest processed data.'

    def handle(self, *args, **options):
        processed_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'processed_data')

        if not os.path.exists(processed_data_path):
            self.stdout.write(self.style.WARNING('Processed data directory not found.'))
            return

        for filename in os.listdir(processed_data_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(processed_data_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            products = data.get('products', [])
            store_id = metadata.get('store_id')

            if not all([metadata, products, store_id]):
                self.stdout.write(self.style.WARNING(f'Skipping {filename}: missing metadata, products, or store_id.'))
                continue

            try:
                store_obj = Store.objects.get(id=store_id)
                company_obj = store_obj.company
            except Store.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Store with ID {store_id} from file {filename} not found in DB. Skipping.'))
                continue

            self.stdout.write(self.style.SUCCESS(f'--- Processing file: {filename} for store: {store_obj.name} ---'))

            with transaction.atomic():
                num_deactivated = deactivate_prices_for_store(store_obj)
                self.stdout.write(f'  Deactivated {num_deactivated} prices for {store_obj.name}')

                product_count = 0
                for product_data in products:
                    category_path = product_data.get('category_path', [])
                    if not category_path:
                        self.stdout.write(self.style.WARNING(f"    - Product '{product_data.get('name')}' is missing category_path. Skipping."))
                        continue

                    # Get or create the category hierarchy
                    category_obj = get_or_create_category_hierarchy(category_path, company_obj)
                    
                    # Get or create the product
                    product_obj, created = get_or_create_product(product_data, store_obj, category_obj)
                    if created:
                        self.stdout.write(f'    - Created new product: {product_obj}')
                    
                    # Create the new price record
                    create_price(product_data, product_obj, store_obj)
                    product_count += 1

            self.stdout.write(self.style.SUCCESS(f'  Successfully processed {product_count} products for store: {store_obj.name}'))

        self.stdout.write(self.style.SUCCESS("\n--- Database update complete ---"))
