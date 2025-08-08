import json
from django.core.management.base import BaseCommand
from api.scrapers.scrape_and_save_aldi import scrape_and_save_aldi_data
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Scrapes ALDI product data for a specific state, based on the aldi_stores_by_state.json file.'

    def handle(self, *args, **options):
        self.stdout.write("Starting ALDI scraper command...")

        # --- Configuration ---
        COMPANY = 'aldi'
        STORES_JSON_PATH = os.path.join('api', 'data', 'store_data', 'stores_aldi', 'aldi_stores_by_state.json')
        SAVE_PATH = os.path.join('api', 'data', 'raw_data', 'aldi')

        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)

        # 1. Read the stores_by_state file
        try:
            with open(STORES_JSON_PATH, 'r') as f:
                stores_data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {STORES_JSON_PATH}. Please run find_aldi_stores first."))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Error decoding JSON from {STORES_JSON_PATH}."))
            return

        # 2. Determine the next state to scrape
        metadata = stores_data.get('metadata', {})
        stores_by_state = stores_data.get('stores_by_state', {})
        
        # Get the list of all states from the data
        all_states = list(stores_by_state.keys())
        if not all_states:
            self.stderr.write(self.style.ERROR("No states found in the JSON file."))
            return

        next_state = metadata.get('next_state_to_scrape')

        # If next_state is not defined or not in our list, start from the first state
        if not next_state or next_state not in all_states:
            next_state = all_states[0]

        self.stdout.write(f"Scraping stores for state: {next_state}")

        # 3. Get the list of stores for the target state
        stores_to_scrape = stores_by_state.get(next_state, [])
        if not stores_to_scrape:
            self.stdout.write(self.style.WARNING(f"No stores found for state: {next_state}"))
        else:
            # 4. Iterate and scrape
            for store in stores_to_scrape:
                store_name = store.get('store_name')
                store_id = store.get('store_id')
                
                if not store_name or not store_id:
                    self.stdout.write(self.style.WARNING(f"Skipping a store due to missing name or ID: {store}"))
                    continue

                self.stdout.write(f"-- Scraping {store_name} ({store_id}) --")
                scrape_and_save_aldi_data(
                    company=COMPANY,
                    store_name=store_name,
                    store_id=store_id,
                    state=next_state,
                    save_path=SAVE_PATH
                )
                self.stdout.write(f"-- Finished scraping {store_name} --\n")

        # 5. Update the metadata for the next run
        current_index = all_states.index(next_state)
        next_index = (current_index + 1) % len(all_states) # Loop back to the start
        metadata['next_state_to_scrape'] = all_states[next_index]
        metadata['last_scraped_timestamp'] = datetime.now().isoformat()
        metadata['last_scraped_state'] = next_state

        try:
            with open(STORES_JSON_PATH, 'w') as f:
                json.dump(stores_data, f, indent=4)
            self.stdout.write(self.style.SUCCESS(f"Successfully updated metadata. Next state to scrape is {all_states[next_index]}."))
        except IOError as e:
            self.stderr.write(self.style.ERROR(f"Could not write updated metadata to {STORES_JSON_PATH}: {e}"))

        self.stdout.write(self.style.SUCCESS("ALDI scraper command finished."))
