import random
import os
from datetime import datetime
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.StoreCleanerWoolworths import StoreCleanerWoolworths
import json

import requests

class StoreScraperWoolworths(BaseStoreScraper):
    """
    A class to scrape Woolworths store data.
    """
    def __init__(self, command):
        super().__init__(command, 'woolworths', progress_file_name='find_woolworths_stores_progress')
        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })
        self.api_url = "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores"
        self.lat_min = -42.0
        self.lat_max = -10.0
        self.lon_min = 112.0
        self.lon_max = 154.0
        self.lat_step = random.uniform(0.25, 0.75)
        self.lon_step = random.uniform(0.25, 0.75)
        self.woolworths_ids = set()
        self.ids_file = "woolworths1_ids.txt"

    def setup(self):
        """Initial setup for the Woolworths scraper."""
        self.stdout.write("\nStarting Woolworths store data scraping...")
        if os.path.exists(self.ids_file):
            with open(self.ids_file, 'r') as f:
                self.woolworths_ids = {line.strip() for line in f if line.strip()}

    def get_work_items(self) -> list:
        """Generates a grid of coordinates to scrape."""
        lat_steps = list(self.drange(self.lat_min, self.lat_max, self.lat_step))
        lon_steps = list(self.drange(self.lon_min, self.lon_max, self.lon_step))
        return [(lat, lon) for lat in lat_steps for lon in lon_steps]

    def fetch_data_for_item(self, item) -> list:
        """Fetches store data for a given coordinate."""
        lat, lon = item
        params = {
            "latitude": lat,
            "longitude": lon,
            "Max": 10000,
            "Division": "SUPERMARKETS,EG,AMPOL",
            "Facility": "",
        }
        try:
            response = self.session.get(self.api_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            stores = data.get("Stores", [])
            for store in stores:
                if store_id := store.get("StoreNo"):
                    self.woolworths_ids.add(str(store_id))
            return stores
        except Exception as e:
            self.stdout.write(f"Request failed: {e}")
            return []


    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw Woolworths store data."""
        cleaner = StoreCleanerWoolworths(raw_data, self.company, datetime.now())
        return cleaner.clean()

    def save_progress(self, completed_steps):
        """Saves progress and updates the store IDs file."""
        super().save_progress(completed_steps)
        with open(self.ids_file, 'w') as f:
            for store_id in sorted(list(self.woolworths_ids)):
                f.write(f"{store_id}\n")

    def cleanup(self):
        """Calls the base cleanup."""
        super().cleanup()

    def get_item_type(self) -> str:
        return "Coords"

    def drange(self, start, stop, step):
        """A simple generator for float ranges."""
        r = start
        while r <= stop:
            yield r
            r += step

def find_woolworths_stores(command):
    """Main function to drive the Woolworths store scraping process."""
    scraper = StoreScraperWoolworths(command)
    scraper.run()