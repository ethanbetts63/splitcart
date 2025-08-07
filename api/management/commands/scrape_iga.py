import os
import json
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_iga import scrape_and_save_iga_data
from api.utils.management_utils.create_store_slug_iga import create_store_slug_iga

class Command(BaseCommand):
    help = 'Launches a long-running scraper to fetch data from two IGA stores per state.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting full IGA scraping cycle (2 stores per state) ---"))

        company_name = "iga"
        stores_file_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'store_data', 'stores_iga', 'iga_stores_by_state.json')

        # 1. Read the combined store and metadata file once
        try:
            with open(stores_file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Store file not found at {stores_file_path}."))
            return

        metadata = data['metadata']
        stores_by_state = data['stores_by_state']
        state_keys = list(stores_by_state.keys())

        if not state_keys:
            self.stdout.write(self.style.ERROR("No states found in the store file."))
            return

        # --- Main scraping loop for all states ---
        for state_key in state_keys:
            self.stdout.write(self.style.SUCCESS(f"\n--- Processing state: {state_key} ---"))

            # Scrape 2 stores from the current state
            for i in range(2):
                stores_in_current_state = stores_by_state[state_key]
                if not stores_in_current_state:
                    self.stdout.write(self.style.WARNING(f"No more stores available in {state_key} for this cycle."))
                    break # Exit the loop for this state

                store_to_scrape = stores_in_current_state[0]
                store_name_slug = create_store_slug_iga(store_to_scrape['store_name'])
                store_id = store_to_scrape['store_id']

                self.stdout.write(f"Attempting to scrape store {i+1}/2: {store_to_scrape['store_name']} ({store_id})")

                raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
                os.makedirs(raw_data_path, exist_ok=True)

                try:
                    scrape_and_save_iga_data(company_name, store_id, store_to_scrape['store_name'], store_name_slug, state_key, raw_data_path)
                    self.stdout.write(self.style.SUCCESS(f"  Successfully scraped {store_to_scrape['store_name']}"))
                    metadata['total_stores_scraped'] += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  An error occurred while scraping {store_to_scrape['store_name']}: {e}"))

                # Always rotate the store to the end of the list
                stores_by_state[state_key].append(stores_by_state[state_key].pop(0))
                metadata['last_scraped_timestamp'] = datetime.datetime.now().isoformat()

        # After the full loop, set the next state for the *next* run of this command
        metadata['next_state_to_scrape'] = state_keys[0]

        # 5. Write the updated data back to the file once at the end
        with open(stores_file_path, 'w') as f:
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f"\n--- Full scraping cycle complete. State file has been updated. ---"))
