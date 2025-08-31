from datetime import datetime
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.woolworths.clean_raw_store_data_woolworths import clean_raw_store_data_woolworths

class WoolworthsStoreScraper2(BaseStoreScraper):
    """
    A class to scrape Woolworths store data using postcodes.
    """
    def __init__(self, command):
        super().__init__(command, 'woolworths')
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
            return data.get("Stores", [])
        except Exception as e:
            self.stdout.write(f"Request failed for postcode {postcode}: {e}")
            return []

    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw Woolworths store data."""
        return clean_raw_store_data_woolworths(raw_data, self.company, datetime.now())

    def print_progress(self, iteration, total, item):
        """Prints the progress of the Woolworths scraper."""
        postcode = item
        percentage = 100 * (iteration / total)
        bar_length = 40
        filled_length = int(bar_length * iteration // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        self.stdout.write(f'Progress: |{bar}| {percentage:.2f}% ({iteration}/{total}) | Stores Found: {self.found_stores} | Postcode: {postcode}')
        self.stdout.flush()

def find_woolworths_stores2(command):
    """Main function to drive the Woolworths store scraping process."""
    scraper = WoolworthsStoreScraper2(command)
    scraper.run()
