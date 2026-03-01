import os
import json
import math
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes
from scraping.utils.coles_session_manager import ColesSessionManager
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter

class ColesScraperV2(BaseProductScraper):
    """
    A refactored scraper for Coles stores that relies on an external session manager.
    This class is responsible only for fetching and processing data for a single store,
    assuming a valid session is provided.
    """

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list, session: requests.Session, session_manager: ColesSessionManager):
        super().__init__(command, company, store_id, store_name, state)
        self.categories_to_fetch = categories_to_fetch
        self.session = session
        self.session_manager = session_manager

    def setup(self):
        """
        Initializes the JsonlWriter for this specific store run.
        """
        numeric_store_id = self.store_id.split(':')[-1] if self.store_id and ':' in self.store_id else self.store_id
        store_name_slug = f"{slugify(self.store_name)}-{numeric_store_id}"
        
        # This scraper's output is intended for the barcode scraper's inbox
        barcode_inbox_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'inboxes', 'barcode_scraper_inbox')
        os.makedirs(barcode_inbox_path, exist_ok=True)
            
        self.jsonl_writer = JsonlWriter(
            self.company, 
            store_name_slug, 
            self.state,
            final_outbox_path=barcode_inbox_path
        )
        return True

    def get_work_items(self) -> list:
        """Returns the list of categories to scrape."""
        return self.categories_to_fetch

    def fetch_data_for_item(self, item) -> list:
        """
        Fetches the raw product data for a single Coles category.
        Checks for session blocks during operation.
        """
        category_slug = item
        all_raw_products = []
        page_num = 1
        total_pages = 1

        while True:
            if page_num > total_pages and total_pages > 1:
                break

            browse_url = f"https://www.coles.com.au/browse/{category_slug}?page={page_num}"
            
            try:
                response = self.session.get(browse_url, timeout=30)
                
                # Check for session block before proceeding
                if self.session_manager.is_blocked(response.text):
                    raise InterruptedError("Session appears to be blocked by CAPTCHA.")

                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                
                if not json_element:
                    break # Category likely has no products or page is empty

                full_data = json.loads(json_element.string)

                # At the start of scraping a new category, verify the store ID hasn't drifted
                if page_num == 1:
                    numeric_store_id = self.store_id.split(':')[-1]
                    actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                    if str(actual_store_id) != str(numeric_store_id):
                        self.command.stderr.write(self.command.style.ERROR(
                            f"Store ID mismatch! Expected {numeric_store_id}, found {actual_store_id}. "
                            "This may indicate a session issue."
                        ))
                        # In this new model, we don't halt, but we warn, as the controlling
                        # loop might need to decide what to do. For now, we stop this category.
                        break
                
                search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                raw_product_list = search_results.get("results", [])

                if not raw_product_list:
                    break

                if page_num == 1:
                    total_results = search_results.get("noOfResults", 0)
                    page_size = search_results.get("pageSize", 48)
                    if total_results > 0 and page_size > 0:
                        total_pages = math.ceil(total_results / page_size)

                all_raw_products.extend(raw_product_list)

            except requests.exceptions.RequestException as e:
                self.command.stderr.write(self.command.style.ERROR(f"Request failed for {category_slug}: {e}"))
                # We break on network errors for this category and move to the next.
                break
            
            page_num += 1
        
        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
        """Cleans the raw Coles product data."""
        from datetime import datetime
        cleaner = DataCleanerColes(
            raw_product_list=raw_data,
            company=self.company,
            store_id=self.store_id,
            store_name=self.store_name,
            state=self.state,
            timestamp=datetime.now(),
            brand_translations=self.brand_translations,
            product_translations=self.product_translations,
        )
        return cleaner.clean_data()
