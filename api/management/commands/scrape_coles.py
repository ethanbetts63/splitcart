import os
import json
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from api.scrapers.scrape_and_save_coles import scrape_and_save_coles_data

class Command(BaseCommand):
    help = 'Launches the Selenium scraper to fetch data from the next Coles store in the rotation.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Coles scraping process ---"))

        company_name = "coles"
        stores_file_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'store_data', 'stores_coles', 'coles_stores_by_state.json')

        # 1. Read the combined store and metadata file
        with open(stores_file_path, 'r') as f:
            data = json.load(f)

        metadata = data['metadata']
        stores_by_state = data['stores_by_state']
        
        current_state_key = metadata['next_state_to_scrape']
        state_keys = list(stores_by_state.keys())

        if current_state_key not in state_keys:
            self.stdout.write(self.style.ERROR(f"State '{current_state_key}' not found. Defaulting to first state."))
            current_state_key = state_keys[0]

        # 2. Get the next store to scrape
        stores_in_current_state = stores_by_state[current_state_key]
        if not stores_in_current_state:
            self.stdout.write(self.style.WARNING(f"No stores listed for {current_state_key}. Skipping to next state."))
        else:
            store_to_scrape = stores_in_current_state[0]
            store_name = store_to_scrape['store_name']
            store_id = store_to_scrape['store_id']

            self.stdout.write(self.style.SUCCESS(f"\n--- Preparing to scrape store: {store_name} ({store_id}) in {current_state_key} ---"))

            categories = [
                "meat-seafood", "fruit-vegetables", "dairy-eggs-fridge", "bakery",
                "deli", "pantry", "dietary-world-foods", "chips-chocolates-snacks",
                "drinks", "frozen", "household", "health-beauty", "baby", "pet", "liquorland",
            ]
            raw_data_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'raw_data')
            os.makedirs(raw_data_path, exist_ok=True)

            # 3. Scrape the store
            try:
                scrape_and_save_coles_data(company_name, store_name, categories, raw_data_path, store_id)
                self.stdout.write(self.style.SUCCESS(f"--- Successfully scraped {store_name} ---"))

                # On success, rotate the list and update metadata
                stores_by_state[current_state_key].append(stores_by_state[current_state_key].pop(0))
                metadata['total_stores_scraped'] += 1
                metadata['last_scraped_timestamp'] = datetime.datetime.now().isoformat()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred while scraping {store_name}: {e}"))
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
