import os
import json
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga

class Command(BaseCommand):
    help = 'Launches the scraper to fetch data from the next IGA store in the rotation.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IGA scraping process ---"))

        company_name = "iga"
        stores_file_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'store_data', 'stores_iga', 'iga_stores_by_state.json')

        # 1. Read the combined store and metadata file
        try:
            with open(stores_file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Store file not found at {stores_file_path}. Please generate it first."))
            return

        metadata = data['metadata']
        stores_by_state = data['stores_by_state']
        
        current_state_key = metadata['next_state_to_scrape']
        state_keys = list(stores_by_state.keys())

        if not state_keys:
            self.stdout.write(self.style.ERROR("No states found in the store file."))
            return

        if current_state_key not in state_keys:
            self.stdout.write(self.style.ERROR(f"State '{current_state_key}' not found. Defaulting to first state."))
            current_state_key = state_keys[0]

        # 2. Get the next store to scrape
        stores_in_current_state = stores_by_state[current_state_key]
        if not stores_in_current_state:
            self.stdout.write(self.style.WARNING(f"No stores listed for {current_state_key}. Skipping to next state."))
        else:
            store_to_scrape = stores_in_current_state[0]
            # Use the slug for file system and checkpoint compatibility
            store_name_slug = create_store_slug_iga(store_to_scrape['store_name'])
            store_id = store_to_scrape['store_id']

            self.stdout.write(self.style.SUCCESS(f"\n--- Preparing to scrape store: {store_to_scrape['store_name']} ({store_id}) in {current_state_key} ---"))

            raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
            os.makedirs(raw_data_path, exist_ok=True)

            # 3. Scrape the store
            try:
                # The scraper function expects a list of stores
                store_list_for_scraper = [{'store_name': store_name_slug, 'store_id': store_id}]
                scrape_and_save_iga_data(company_name, store_list_for_scraper, raw_data_path)
                self.stdout.write(self.style.SUCCESS(f"--- Successfully scraped {store_to_scrape['store_name']} ---"))

                # On success, rotate the list and update metadata
                stores_by_state[current_state_key].append(stores_by_state[current_state_key].pop(0))
                metadata['total_stores_scraped'] += 1
                metadata['last_scraped_timestamp'] = datetime.datetime.now().isoformat()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred while scraping {store_to_scrape['store_name']}: {e}"))
                # On failure, do not update the file, so we can retry the same store next time
                return

        # 4. Determine the next state for the next run
        current_index = state_keys.index(current_state_key)
        next_index = (current_index + 1) % len(state_keys)
        metadata['next_state_to_scrape'] = state_keys[next_index]

        # 5. Write the updated data back to the file
        with open(stores_file_path, 'w') as f:
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f"\n--- Rotation complete. Next scrape will be in: {metadata['next_state_to_scrape']} ---"))