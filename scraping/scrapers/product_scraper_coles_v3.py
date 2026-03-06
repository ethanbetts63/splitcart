import os
import json
import math
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes
from scraping.utils.coles_session_manager import ColesSessionManager
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter


class ColesScraperV3(BaseProductScraper):
    """
    Same as v2 but fetches all categories in parallel using threads.
    All 15 categories are fetched concurrently, then cleaned and written
    sequentially. Faster than v2 by roughly the number of parallel workers.
    """

    MAX_WORKERS = 5

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str,
                 categories_to_fetch: list, session: requests.Session, session_manager: ColesSessionManager):
        super().__init__(command, company, store_id, store_name, state)
        self.categories_to_fetch = categories_to_fetch
        self.session = session
        self.session_manager = session_manager

    def setup(self):
        numeric_store_id = self.store_id.split(':')[-1] if self.store_id and ':' in self.store_id else self.store_id
        store_name_slug = f"{slugify(self.store_name)}-{numeric_store_id}"

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
        return self.categories_to_fetch

    def fetch_data_for_item(self, item) -> list:
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

                if self.session_manager.is_blocked(response.text):
                    raise InterruptedError("Session appears to be blocked by CAPTCHA.")

                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                json_element = soup.find('script', {'id': '__NEXT_DATA__'})

                if not json_element:
                    break

                full_data = json.loads(json_element.string)

                if page_num == 1:
                    numeric_store_id = self.store_id.split(':')[-1]
                    actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                    if str(actual_store_id) != str(numeric_store_id):
                        self.command.stderr.write(self.command.style.ERROR(
                            f"Store ID mismatch! Expected {numeric_store_id}, found {actual_store_id}."
                        ))
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
                break

            page_num += 1

        return all_raw_products

    def run(self):
        """
        Overrides the base run() to fetch all categories in parallel, then
        clean and write results sequentially.
        """
        scrape_successful = False
        if not self.setup():
            self.command.stdout.write(self.command.style.ERROR("Setup failed, aborting scrape."))
            return

        try:
            self.jsonl_writer.open()
            work_items = self.get_work_items()
            self.output.update_progress(total_categories=len(work_items))

            # Fetch all categories concurrently
            results = {}
            fetched = 0
            self.command.stdout.write(f"Fetching {len(work_items)} categories with {self.MAX_WORKERS} threads...")
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                future_to_item = {executor.submit(self.fetch_data_for_item, item): item for item in work_items}
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    data = future.result()  # re-raises InterruptedError if a thread hit a block
                    results[item] = data
                    fetched += 1
                    self.command.stdout.write(f"  [{fetched}/{len(work_items)}] {item}: {len(data)} products")

            # Clean and write sequentially in original category order
            for i, item in enumerate(work_items):
                self.output.update_progress(categories_scraped=i + 1)
                raw_data_list = results.get(item, [])

                if not raw_data_list:
                    continue

                try:
                    cleaned_data_packet = self.clean_raw_data(raw_data_list)
                    if cleaned_data_packet and cleaned_data_packet.get('products'):
                        self.write_data(cleaned_data_packet)
                except Exception as e:
                    self.command.stderr.write(self.command.style.ERROR(f"Error cleaning data for {item}: {e}"))
                    import traceback
                    self.command.stderr.write(traceback.format_exc())
                    break

            if self.output.new_products > 0 or self.output.duplicate_products > 0:
                scrape_successful = True

        finally:
            if self.jsonl_writer:
                self.jsonl_writer.close()
                if scrape_successful:
                    self.post_scrape_enrichment()
                    self.jsonl_writer.commit()
                else:
                    self.jsonl_writer.cleanup()
            self.output.finalize()

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
