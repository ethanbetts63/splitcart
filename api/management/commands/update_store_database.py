import json
import os
from django.core.management.base import BaseCommand

from api.utils.database_updating_utils.get_or_create_company import get_or_create_company
from api.utils.database_updating_utils.get_or_create_division import get_or_create_division
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

class Command(BaseCommand):
    help = 'Updates the store database from files in the discovered_stores directory.'

    def handle(self, *args, **options):
        DISCOVERED_STORES_DIR = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\discovered_stores"

        if not os.path.exists(DISCOVERED_STORES_DIR):
            self.stdout.write(self.style.WARNING(f"'{DISCOVERED_STORES_DIR}' not found. Nothing to process."))
            return

        store_files = [f for f in os.listdir(DISCOVERED_STORES_DIR) if f.endswith('.json')]

        if not store_files:
            self.stdout.write(self.style.SUCCESS("No new store files found in discovered_stores."))
            return

        # Process only the first file for now, as per the request
        file_to_process = store_files[0]
        file_path = os.path.join(DISCOVERED_STORES_DIR, file_to_process)

        self.stdout.write(self.style.SUCCESS(f"Processing file: {file_to_process}"))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                store_data_full = json.load(f)

            metadata = store_data_full.get('metadata', {})
            store_data = store_data_full.get('store_data', {})

            company_name = metadata.get('company')
            division_name = store_data.get('division') # Assuming division is in store_data
            store_id = store_data.get('store_id')

            if not company_name or not store_id:
                self.stdout.write(self.style.ERROR(f"Skipping {file_to_process}: Missing company name or store ID."))
                os.remove(file_path) # Remove problematic file
                return

            # 1. Get or Create Company
            company_obj, company_created = get_or_create_company(company_name)
            if company_created:
                self.stdout.write(self.style.SUCCESS(f"Created new Company: {company_obj.name}"))

            # 2. Get or Create Division (if division_name exists)
            division_obj = None
            if division_name:
                division_obj, division_created = get_or_create_division(company_obj, division_name)
                if division_created:
                    self.stdout.write(self.style.SUCCESS(f"Created new Division: {division_obj.name} for {company_obj.name}"))

            # 3. Get or Create/Update Store
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

            # 4. Delete processed file
            os.remove(file_path)
            self.stdout.write(self.style.SUCCESS(f"Successfully processed and deleted {file_to_process}"))

        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Error decoding JSON from {file_to_process}. File might be corrupted. Removing."))
            os.remove(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred while processing {file_to_process}: {e}"))
            # Optionally, move to an error directory instead of deleting
            # For now, just remove to prevent reprocessing the same error
            os.remove(file_path)
