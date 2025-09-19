import os
import json
import math
import requests
from bs4 import BeautifulSoup
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.scrapers.base_product_scraper import BaseProductScraper
from api.utils.scraper_utils.DataCleanerColes import DataCleanerColes
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.scrapers.barcode_scraper_coles import ColesBarcodeScraper

class ColesScraper(BaseProductScraper):
    """
    A scraper for Coles stores, using the BaseProductScraper class.
    """

    def __init__(self, command, company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list):
        super().__init__(command, company, store_id, store_name, state)
        self.session = None
        self.categories_to_fetch = categories_to_fetch

    def setup(self):
        """
        Launches a browser for session setup, then creates a requests session.
        """
        numeric_store_id = self.store_id.split(':')[-1] if self.store_id and ':' in self.store_id else self.store_id
        store_name_slug = f"{slugify(self.store_name)}-{numeric_store_id}"
        self.jsonl_writer = JsonlWriter(self.company, store_name_slug, self.state)

        driver = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            
            driver.get("https://www.coles.com.au")
            
            driver.delete_all_cookies()
            driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
            driver.refresh()

            self.command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.\n")
            self.command.stdout.write("Waiting for __NEXT_DATA__ script to appear (indicating main page load).\n")
            
            WebDriverWait(driver, 300, poll_frequency=2).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )

            self.session = requests.Session()
            self.session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])

            driver.quit()
            driver = None

        except Exception as e:
            if driver:
                driver.quit()
            self.command.stdout.write(f"A critical error occurred during the Selenium phase: {e}\n")
            raise e

        return True

    def get_work_items(self) -> list:
        """Returns the list of categories to scrape."""
        return self.categories_to_fetch

    def fetch_data_for_item(self, item) -> list:
        """Fetches the raw product data for a single Coles category."""
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
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                
                if not json_element:
                    break

                full_data = json.loads(json_element.string)

                if page_num == 1:
                    numeric_store_id = self.store_id.split(':')[-1] if self.store_id and ':' in self.store_id else self.store_id
                    actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                    if str(actual_store_id) != str(numeric_store_id):
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

            except (requests.exceptions.RequestException, Exception):
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
            timestamp=datetime.now()
        )
        return cleaner.clean_data()

    def post_scrape_enrichment(self):
        """Enriches the scraped data with barcode information."""
        temp_file_path = self.jsonl_writer.temp_file_path
        try:
            self.command.stdout.write(self.command.style.SQL_FIELD(f"--- Handing over {os.path.basename(temp_file_path)} for barcode enrichment ---"))
            
            # Instantiate and run the barcode scraper directly
            barcode_scraper = ColesBarcodeScraper(command=self.command, source_file_path=temp_file_path)
            barcode_scraper.run()

            self.command.stdout.write(self.command.style.SUCCESS(f"--- Enrichment complete. Committing {os.path.basename(temp_file_path)} to inbox. ---"))
        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"\nBarcode enrichment failed: {e}"))
            raise e
