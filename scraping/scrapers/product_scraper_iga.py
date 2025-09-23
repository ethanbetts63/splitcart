import requests
import json
import time
import random
import uuid
from datetime import datetime
from django.utils.text import slugify
from api.scrapers.base_product_scraper import BaseProductScraper
from api.utils.scraper_utils.DataCleanerIga import DataCleanerIga
from api.utils.scraper_utils.get_iga_categories import get_iga_categories
from api.utils.scraper_utils.jsonl_writer import JsonlWriter

class IgaScraper(BaseProductScraper):
    """
    A scraper for IGA stores.
    """
    def __init__(self, command, company: str, store_id: str, retailer_store_id: str, store_name: str, state: str):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None
        self.retailer_store_id = retailer_store_id

    def setup(self):
        """
        Initializes the requests.Session and the JsonlWriter.
        """
        if not self.retailer_store_id:
            self.output.log_error("Retailer store ID is missing.")
            return False

        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
            "x-shopping-mode": "11111111-1111-1111-1111-111111111111"
        })
        self.session.cookies.set("iga-shop.retailerStoreId", self.retailer_store_id)

        try:
            self.session.get("https://www.igashop.com.au/", timeout=60)
        except requests.exceptions.RequestException as e:
            self.output.log_error(f"Failed to initialize session: {e}")
            return False

        store_name_slug = slugify(self.store_name.lower().replace('iga', '').replace('fresh', ''))
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)
        return True

    def get_work_items(self) -> list:
        """
        Fetches the list of IGA categories to scrape.
        """
        return get_iga_categories(self.command, self.retailer_store_id, self.session)

    def fetch_data_for_item(self, item) -> list:
        """
        Fetches the raw product data for a single IGA category.
        """
        category_identifier = item['identifier']
        all_raw_products = []
        session_id = str(uuid.uuid4())
        
        take = 36
        skip = 0
        previous_page_skus = set()

        while True:
            api_url = f"https://www.igashop.com.au/api/storefront/stores/{self.retailer_store_id}/categories/{requests.utils.quote(category_identifier)}/search"
            params = {'take': take, 'skip': skip, 'sessionId': session_id}

            try:
                response = self.session.get(api_url, params=params, timeout=60)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = data.get("items", [])
                if not raw_products_on_page:
                    break

                current_page_skus = {p.get('sku') for p in raw_products_on_page}
                if current_page_skus == previous_page_skus:
                    break
                previous_page_skus = current_page_skus

                all_raw_products.extend(raw_products_on_page)

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                self.output.log_error(f"Error fetching data for category {category_identifier}: {e}")
                break

            time.sleep(random.uniform(0.5, 1.5))
            skip += take
        
        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
        """
        Cleans the raw IGA product data.
        """
        cleaner = DataCleanerIga(
            raw_product_list=raw_data,
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            timestamp=datetime.now()
        )
        return cleaner.clean_data()
