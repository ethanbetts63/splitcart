import math
import os
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter
from scraping.utils.coles_browser_session_v5 import ColesBrowserSessionV5


class ColesScraperV5(BaseProductScraper):
    """
    Coles scraper using the browser's fetch() API with string-based __NEXT_DATA__
    extraction (no DOMParser). Fetches the full HTML browse page but extracts
    the JSON payload via string search, which is significantly faster than
    building a full DOM tree.

    Returns the same __NEXT_DATA__ structure as v3 (props.pageProps wrapper).
    """

    def __init__(self, command, company: str, store_id: str, store_name: str,
                 state: str, categories_to_fetch: list, browser_session: ColesBrowserSessionV5):
        super().__init__(command, company, store_id, store_name, state)
        self.categories_to_fetch = categories_to_fetch
        self.browser_session = browser_session

    def setup(self):
        numeric_id = self.store_id.split(':')[-1] if ':' in self.store_id else self.store_id
        store_name_slug = f"{slugify(self.store_name)}-{numeric_id}"

        barcode_inbox_path = os.path.join(
            settings.BASE_DIR, 'scraping', 'data', 'inboxes', 'barcode_scraper_inbox'
        )
        os.makedirs(barcode_inbox_path, exist_ok=True)

        self.jsonl_writer = JsonlWriter(
            self.company,
            store_name_slug,
            self.state,
            final_outbox_path=barcode_inbox_path,
        )

        self.browser_session.switch_store(self.store_id)
        return True

    def get_work_items(self) -> list:
        return self.categories_to_fetch

    def fetch_data_for_item(self, item) -> list:
        category_slug = item
        all_raw_products = []
        page_num = 1
        total_pages = 1

        while True:
            if page_num > total_pages and total_pages > 1:
                break

            url = f"https://www.coles.com.au/browse/{category_slug}?page={page_num}"
            full_data = self.browser_session.fetch_browse_page(url)

            if full_data is None:
                raise InterruptedError(
                    f"Browser fetch returned None for {category_slug} page {page_num}."
                )

            # fetch() returns full __NEXT_DATA__, same structure as v3
            page_props = full_data.get("props", {}).get("pageProps", {})

            if page_num == 1:
                numeric_id = self.store_id.split(':')[-1] if ':' in self.store_id else self.store_id
                actual_store_id = page_props.get("initStoreId")
                if int(actual_store_id) != int(numeric_id):
                    self.command.stderr.write(self.command.style.ERROR(
                        f"Store ID mismatch: expected {numeric_id}, got {actual_store_id}."
                    ))
                    break

            search_results = page_props.get("searchResults", {})
            raw_product_list = search_results.get("results", [])

            if not raw_product_list:
                break

            if page_num == 1:
                total_results = search_results.get("noOfResults", 0)
                page_size = search_results.get("pageSize", 48)
                if total_results > 0 and page_size > 0:
                    total_pages = math.ceil(total_results / page_size)

            all_raw_products.extend(raw_product_list)
            page_num += 1

        return all_raw_products

    def clean_raw_data(self, raw_data: list) -> dict:
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
