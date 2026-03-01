import requests
import time
import random
from datetime import datetime
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerAldi import DataCleanerAldi
from scraping.utils.product_scraping_utils.get_aldi_categories import get_aldi_categories
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter

class ProductScraperAldi(BaseProductScraper):
    """
    A scraper for ALDI stores.
    """

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None

    def setup(self):
        """
        Initializes the requests.Session and the JsonlWriter.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })
        
        effective_store_name = self.store_name if self.store_name else f"ALDI Store {self.store_id}"
        store_name_slug = f"{slugify(effective_store_name)}-{self.store_id}"
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)
        return True

    def get_work_items(self) -> list:
        """
        Fetches the list of ALDI categories to scrape.
        """
        return get_aldi_categories(self.command, self.store_id, self.session)

    def fetch_data_for_item(self, item) -> list:
        """
        Fetches the raw product data for a single ALDI category.
        """
        category_slug, category_key = item
        all_raw_products = []
        
        limit = 30
        offset = 0

        while True:
            api_url = "https://api.aldi.com.au/v3/product-search"
            params = {
                "currency": "AUD", "serviceType": "walk-in", "categoryKey": category_key,
                "limit": limit, "offset": offset, "sort": "relevance", "testVariant": "A",
                "servicePoint": self.store_id,
            }

            try:
                response = self.session.get(api_url, params=params, timeout=60)
                if response.status_code == 400:
                    break
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = data.get("data", [])

                if not raw_products_on_page:
                    break

                all_raw_products.extend(raw_products_on_page)

            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as e:
                self.output.log_error(f"Error fetching data for category {category_slug}: {e}")
                break

            time.sleep(random.uniform(0.5, 1.5))
            
            offset += limit
        
        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
        """
        Cleans the raw ALDI product data.
        """
        effective_store_name = self.store_name if self.store_name else f"ALDI Store {self.store_id}"
        cleaner = DataCleanerAldi(
            raw_product_list=raw_data,
            company=self.company,
            store_name=effective_store_name,
            store_id=self.store_id,
            state=self.state,
            timestamp=datetime.now()
        )
        return cleaner.clean_data()

