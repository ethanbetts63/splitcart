import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from api.utils.database_updating_utils import (
    deactivate_prices_for_store,
    get_or_create_product,
    create_price,
    get_or_create_category_hierarchy
)
from companies.models import Store

class Command(BaseCommand):
    help = 'Updates the database with the latest scraped data.'

    def handle(self, *args, **options):
        processed_data_dir = os.path.join('api', 'data', 'processed_data')

        for company_name in os.listdir(processed_data_dir):
            company_dir = os.path.join(processed_data_dir, company_name)
            if not os.path.isdir(company_dir): continue

            for state_name in os.listdir(company_dir):
                state_dir = os.path.join(company_dir, state_name)
                if not os.path.isdir(state_dir): continue

                for store_id in os.listdir(state_dir):
                    store_dir = os.path.join(state_dir, store_id)
                    if not os.path.isdir(store_dir): continue

                    try:
                        store_obj = Store.objects.get(id=store_id)
                    except Store.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Store with ID {store_id} not found. Skipping.'))
                        continue

                    self.stdout.write(f'Processing data for store: {store_obj.name}')

                    with transaction.atomic():
                        num_deactivated = deactivate_prices_for_store(store_obj)
                        self.stdout.write(self.style.SUCCESS(f'Deactivated {num_deactivated} prices for {store_obj.name}'))

                        for date_folder in os.listdir(store_dir):
                            date_dir = os.path.join(store_dir, date_folder)
                            if not os.path.isdir(date_dir): continue

                            for category_file in os.listdir(date_dir):
                                if not category_file.endswith('.json'): continue

                                file_path = os.path.join(date_dir, category_file)
                                with open(file_path, 'r') as f:
                                    products_data = json.load(f)

                                category_name = os.path.splitext(category_file)[0].replace('-', ' ').title()
                                # This is a placeholder for getting the category object.
                                # You would replace this with your actual category lookup logic.
                                category_obj = get_or_create_category_hierarchy(category_name, store_obj)

                                for product_data in products_data:
                                    product_obj, created = get_or_create_product(product_data, store_obj, category_obj)
                                    if created:
                                        self.stdout.write(f'  Created new product: {product_obj}')
                                    create_price(product_data, product_obj, store_obj)

                    self.stdout.write(self.style.SUCCESS(f'Successfully updated database for store: {store_obj.name}'))