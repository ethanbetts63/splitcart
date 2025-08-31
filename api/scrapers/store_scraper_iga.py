import json
import html
import re
from datetime import datetime
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.clean_raw_store_data_iga import clean_raw_store_data_iga
import requests

class StoreScraperIga(BaseStoreScraper):
    """
    A class to scrape IGA store data.
    """
    def __init__(self, command):
        super().__init__(command, 'iga')
        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })
        self.max_store_id = 23001

    def setup(self):
        """Initial setup for the IGA scraper."""
        self.stdout.write("\nPerforming thorough search for IGA stores...")

    def get_work_items(self) -> list:
        """Generates a list of store IDs to scrape."""
        return list(range(1, self.max_store_id + 1))

    def fetch_data_for_item(self, item) -> list:
        """Fetches store data for a given store ID."""
        store_id_num = item  

        url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id_num}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            jsonp_content = response.text
            start_index = jsonp_content.find('(')
            end_index = jsonp_content.rfind(')')

            if start_index != -1 and end_index != -1:
                json_str = jsonp_content[start_index + 1:end_index]
                data = json.loads(json_str)
                html_content = data.get('content', '')
                return self.parse_and_clean_stores(html_content)
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError):
            pass
        return []

    def parse_and_clean_stores(self, html_content):
        """Parses store data from HTML and returns a cleaned list of store dictionaries."""
        stores = []
        store_data_matches = re.findall(r'data-storedata="([^"]*)"', html_content)
        for store_data_str in store_data_matches:
            decoded_str = html.unescape(store_data_str)
            try:
                store_data = json.loads(decoded_str)
                if 'distance' in store_data:
                    del store_data['distance']
                stores.append(store_data)
            except json.JSONDecodeError as e:
                self.stdout.write(f"\nError decoding JSON: {e}")
                self.stdout.write(f"Problematic string: {decoded_str}")
        return stores

    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw IGA store data."""
        return clean_raw_store_data_iga(raw_data, self.company, datetime.now())

    def get_item_type(self) -> str:
        return "ID"

def find_iga_stores(command):
    """Main function to drive the IGA store scraping process."""
    scraper = StoreScraperIga(command)
    scraper.run()