import json
import os
import time
from django.core.management.base import BaseCommand

from api.utils.database_updating_utils.get_or_create_company import get_or_create_company
from api.utils.database_updating_utils.get_or_create_division import get_or_create_division
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

class Command(BaseCommand):
    help = 'Updates the store database from files in the discovered_stores directory.'

    def process_store_file(self, file_name, directory):
        file_path = os.path.join(directory, file_name)
        self.stdout.write(self.style.SUCCESS(f"Processing file: {file_name}"))
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                store_data_full = json.load(f)

            metadata = store_data_full.get('metadata', {})
            store_data = store_data_full.get('store_data', {})

            company_name = metadata.get('company')
            division_name = store_data.get('division')
            store_id = store_data.get('store_id')

            if not company_name or not store_id:
                self.stdout.write(self.style.ERROR(f"Skipping {file_name}: Missing company name or store ID."))
                os.remove(file_path)
                return

            company_obj, company_created = get_or_create_company(company_name)
            if company_created:
                self.stdout.write(self.style.SUCCESS(f"Created new Company: {company_obj.name}"))

            division_obj = None
            if division_name:
                division_obj, division_created = get_or_create_division(company_obj, division_name)
                if division_created:
                    self.stdout.write(self.style.SUCCESS(f"Created new Division: {division_obj.name} for {company_obj.name}"))

            store_obj, store_created = get_or_create_store(
                company_obj=company_obj,
                division_obj=division_obj,
                store_id=store_id,
                store_data=store_data
            )

            if store_created:
                self.stdout.write(self.style.SUCCESS(f"Created new Store: {store_obj.name} ({store_obj.store_id})"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated existing Store: {store_obj.name} ({store_obj.store_id})"))

            os.remove(file_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully processed and deleted {file_name}"))

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON from {file_name}. Removing."))
            os.remove(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred while processing {file_name}: {e}"))
            os.remove(file_path)

    def handle(self, *args, **options):
        DISCOVERED_STORES_DIR = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\discovered_stores"

        if not os.path.exists(DISCOVERED_STORES_DIR):
            self.stdout.write(self.style.WARNING(f"'{DISCOVERED_STORES_DIR}' not found. Nothing to process."))
            return

        store_files = [f for f in os.listdir(DISCOVERED_STORES_DIR) if f.endswith('.json')]

        if not store_files:
            self.stdout.write(self.style.SUCCESS("No new store files found. Waiting 60 seconds to check again..."))
            time.sleep(60)
            store_files = [f for f in os.listdir(DISCOVERED_STORES_DIR) if f.endswith('.json')]
            if not store_files:
                self.stdout.write(self.style.SUCCESS("No new store files found after waiting. Exiting."))
                return
            self.stdout.write(self.style.SUCCESS("New files found after waiting. Processing..."))

        for file_name in store_files:
            self.process_store_file(file_name, DISCOVERED_STORES_DIR)