import os
from datetime import datetime
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.StoreCleanerWoolworths import StoreCleanerWoolworths
import json
import requests

class StoreScraperWoolworths2(BaseStoreScraper):
    """
    A class to scrape Woolworths store data using postcodes.
    """
    def __init__(self, command):
        super().__init__(command, 'woolworths', progress_file_name='find_woolworths_stores_progress_2')
        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })
        self.api_url = "https://www.woolworths.com.au/api/v3/ui/fulfilment/stores"
        self.raw_response_logged = False
        self.woolworths_ids = set()
        self.ids_file = "woolworths2_ids.txt"

    def setup(self):
        """Initial setup for the Woolworths scraper."""
        self.stdout.write("\nStarting Woolworths store data scraping (postcode method).")
        if os.path.exists(self.ids_file):
            with open(self.ids_file, 'r') as f:
                self.woolworths_ids = {line.strip() for line in f if line.strip()}

    def get_work_items(self) -> list:
        """Generates a list of postcodes to scrape."""
        return list(range(1, 10000, 5))

    def fetch_data_for_item(self, item) -> list:
        """Fetches store data for a given postcode."""
        postcode = item
        params = {
            "postcode": str(postcode).zfill(4)
        }
        try:
            response = self.session.get(self.api_url, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()

            stores_list = []
            if isinstance(data, list):
                stores_list = data
            elif isinstance(data, dict):
                stores_list = data.get("Stores", [])

            for store in stores_list:
                if store_id := store.get("FulfilmentStoreId"):
                    self.woolworths_ids.add(str(store_id))

            if isinstance(data, list):
                return data
            return data.get("Stores", [])
        except Exception as e:
            self.stdout.write(f"Request failed for postcode {postcode}: {e}")
            return []


    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw Woolworths store data."""
        cleaner = StoreCleanerWoolworths(raw_data, self.company, datetime.now())
        return cleaner.clean()

    def cleanup(self):
        """Saves the unique store IDs and then calls the base cleanup."""
        with open(self.ids_file, 'w') as f:
            for store_id in sorted(list(self.woolworths_ids)):
                f.write(f"{store_id}\n")
        super().cleanup()

    def get_item_type(self) -> str:
        return "Postcode"

def find_woolworths_stores2(command):
    """Main function to drive the Woolworths store scraping process."""
    scraper = StoreScraperWoolworths2(command)
    scraper.run()