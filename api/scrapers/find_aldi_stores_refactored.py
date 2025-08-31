
import random
import sys
from datetime import datetime
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.aldi.clean_raw_store_data_aldi import clean_raw_store_data_aldi

class AldiStoreScraper(BaseStoreScraper):
    """
    A class to scrape ALDI store data.
    """
    def __init__(self, command):
        super().__init__(command, 'aldi')
        self.api_url = "https://api.aldi.com.au/v2/service-points"
        self.lat_min = -44.0
        self.lat_max = -10.0
        self.lon_min = 112.0
        self.lon_max = 154.0
        self.lat_step = random.uniform(0.25, 0.75)
        self.lon_step = random.uniform(0.25, 0.75)

    def setup(self):
        """Initial setup for the ALDI scraper."""
        self.stdout.write("\nStarting ALDI store data scraping...")

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
            "serviceType": "walk-in",
            "includeNearbyServicePoints": "true",
        }
        try:
            response = self.session.get(self.api_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            self.stdout.write(f"Request failed: {e}")
            return []

    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw ALDI store data."""
        return clean_raw_store_data_aldi(raw_data, self.company, datetime.now())

    def print_progress(self, iteration, total, item):
        """Prints the progress of the ALDI scraper."""
        lat, lon = item
        percentage = 100 * (iteration / total)
        bar_length = 40
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        self.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% ({iteration}/{total}) | Stores Found: {self.found_stores} | Coords: ({lat:.2f}, {lon:.2f})')
        self.stdout.flush()

    def drange(self, start, stop, step):
        """A simple generator for float ranges."""
        r = start
        while r <= stop:
            yield r
            r += step

def find_aldi_stores(command):
    """Main function to drive the ALDI store scraping process."""
    scraper = AldiStoreScraper(command)
    scraper.run()
