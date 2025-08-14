
import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from api.utils.database_updating_utils import (
    get_or_create_company,
    get_or_create_store,
    get_or_create_division,
)

class Command(BaseCommand):
    help = 'Updates the database from archived JSON files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stores',
            action='store_true',
            help='Update store information from the company_data archive.'
        )
        parser.add_argument(
            '--products',
            action='store_true',
            help='Update products and prices from the store_data archive.'
        )

    def handle(self, *args, **options):
        run_stores = options['stores']
        run_products = options['products']

        # If no flags are specified, run both processes
        if not run_stores and not run_products:
            run_stores = True
            run_products = True

        if run_stores:
            self.update_stores()
        
        if run_products:
            self.stdout.write(self.style.WARNING("Product update from archive is not yet implemented."))

    def update_stores(self):
        self.stdout.write(self.style.SUCCESS("--- Starting Store Update from Archive ---"))
        archive_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'archive', 'company_data')

        if not os.path.exists(archive_path):
            self.stdout.write(self.style.WARNING('Company data archive directory not found.'))
            return

        for filename in os.listdir(archive_path):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(archive_path, filename)
            self.stdout.write(f"Processing file: {filename}")
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    self.stderr.write(self.style.ERROR(f"  Could not decode JSON from {filename}. Skipping."))
                    continue

            metadata = data.get('metadata', {})
            company_name = metadata.get('company_name')
            if not company_name:
                self.stderr.write(self.style.ERROR(f"  Skipping {filename}: missing company_name in metadata."))
                continue

            company_obj, _ = get_or_create_company(company_name)
            stores_by_division = data.get('stores_by_division', {})

            for division_slug, division_data in stores_by_division.items():
                division_name = division_data.get('division_name')
                if not division_name:
                    continue
                
                division_obj, _ = get_or_create_division(division_name, company_obj)

                stores = division_data.get('stores', [])
                store_count = 0
                for store_data in stores:
                    store_id = store_data.get('store_id')
                    if not store_id:
                        continue
                    
                    get_or_create_store(
                        company_obj=company_obj,
                        division_obj=division_obj,
                        store_id=store_id,
                        store_data=store_data
                    )
                    store_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Processed {store_count} stores for division '{division_name}'."))

        self.stdout.write(self.style.SUCCESS("--- Store Update from Archive Complete ---"))
