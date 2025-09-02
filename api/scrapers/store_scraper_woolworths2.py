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

    def setup(self):
        """Initial setup for the Woolworths scraper."""
        self.stdout.write("\nStarting Woolworths store data scraping (postcode method).")

    def get_work_items(self) -> list:
        """Generates a list of postcodes to scrape."""
        return list(range(1, 10000, 10))

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
                if isinstance(store, dict) and not store.get("Division"):
                    with open("woolworths_no_division_response2.jsonl", "a") as f:
                        f.write(json.dumps(data) + '\n')
                    break  # Log the response once

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

    def get_item_type(self) -> str:
        return "Postcode"

def find_woolworths_stores2(command):
    """Main function to drive the Woolworths store scraping process."""
    scraper = StoreScraperWoolworths2(command)
    scraper.run()