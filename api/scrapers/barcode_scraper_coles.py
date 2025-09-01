import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.scrapers.base_product_scraper import BaseProductScraper
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.utils.normalizer import ProductNormalizer
from api.utils.database_updating_utils.prefill_barcodes import prefill_barcodes_from_db

class ColesBarcodeScraper(BaseProductScraper):
    """
    A scraper dedicated to enriching Coles product data with barcode information.
    It reads from an existing .jsonl file, scrapes individual product pages for
    barcodes, and writes the enriched data to a new file.
    """

    def __init__(self, command, source_file_path: str):
        self.command = command
        self.source_file_path = source_file_path
        self.progress_file_path = source_file_path + ".progress"
        self.session = None
        self.jsonl_writer = None
        self.output = None # Will be initialized in setup

        # These will be populated from the source file's metadata
        self.company = "coles"
        self.store_id = None
        self.store_name = None
        self.state = None


    def setup(self):
        """
        Initializes the scraper by setting up the output, loading metadata,
        and preparing the session.
        """
        # --- Step 1: Load Master File and Determine Metadata ---
        try:
            with open(self.source_file_path, 'r') as f:
                # Read the first line to get metadata
                first_line = f.readline()
                if not first_line:
                    raise ValueError("Source file is empty.")
                metadata = json.loads(first_line).get('metadata', {})
                self.store_id = metadata.get('store_id')
                self.store_name = metadata.get('store_name')
                self.state = metadata.get('state')
                if not all([self.store_id, self.store_name, self.state]):
                    raise ValueError("Could not extract required metadata from source file.")
        except (IOError, json.JSONDecodeError, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"CRITICAL: Could not read source file or metadata: {e}"))
            raise InterruptedError from e

        # --- Step 2: Initialize Output and JsonlWriter ---
        super().__init__(self.command, self.company, self.store_id, self.store_name, self.state)
        self.jsonl_writer = JsonlWriter(self.company, f"{self.store_name}-{self.store_id.split(':')[-1]}-barcodes", self.state)

        # --- Step 3: Selenium Session Creation ---
        self.warm_up_session()


    def warm_up_session(self):
        """
        Uses Selenium to solve CAPTCHA and get a valid requests session.
        """
        driver = None
        try:
            numeric_store_id = self.store_id.split(':')[-1]
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            driver.get("https://www.coles.com.au")
            driver.delete_all_cookies()
            driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
            driver.refresh()
            self.command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.")
            WebDriverWait(driver, 300, poll_frequency=2).until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
            self.command.stdout.write("CAPTCHA solved. Creating session...")
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
        except Exception as e:
            raise InterruptedError(f"A critical error occurred during the Selenium phase: {e}")
        finally:
            if driver:
                driver.quit()

        if not self.session:
            raise InterruptedError("Failed to create a requests session. Aborting.")


    def get_work_items(self) -> list:
        """
        Loads the source file, checks against the progress file, and returns a list
        of product data dictionaries that need scraping.
        """
        # --- Step 1: Load Progress Cache ---
        found_products = {}
        if os.path.exists(self.progress_file_path):
            with open(self.progress_file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        sku = data.get('product', {}).get('product_id_store')
                        if sku:
                            found_products[sku] = data
                    except json.JSONDecodeError:
                        continue

        # --- Step 2: Load Master File and Determine Work ---
        try:
            with open(self.source_file_path, 'r') as f:
                master_line_list = [json.loads(line) for line in f if line.strip()]
        except (IOError, json.JSONDecodeError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"CRITICAL: Could not read source file: {e}"))
            return []

        # --- Step 3: Prefill from DB and identify what needs scraping ---
        master_product_list = [line.get('product') for line in master_line_list]
        enriched_master_list = prefill_barcodes_from_db(master_product_list, self.command)
        for i, line_data in enumerate(master_line_list):
            if 'product' in line_data:
                line_data['product'] = enriched_master_list[i]

        lines_to_scrape = []
        for line_data in master_line_list:
            product_info = line_data.get('product', {})
            sku = product_info.get('product_id_store')

            # If already processed in a previous run, skip.
            if sku in found_products:
                self.jsonl_writer.write_product(found_products[sku]['product'], found_products[sku].get('metadata', {}))
                continue

            # If it has a barcode or no URL, it doesn't need scraping.
            if product_info.get('barcode') or not product_info.get('url'):
                self.jsonl_writer.write_product(product_info, line_data.get('metadata', {}))
                continue

            lines_to_scrape.append(line_data)

        self.command.stdout.write(f"Found {len(lines_to_scrape)} products requiring barcode scraping.")
        return lines_to_scrape


    def fetch_data_for_item(self, item) -> list:
        """
        Fetches the barcode for a single product from its URL.
        'item' is the complete line_data dictionary.
        """
        product_data = item['product']
        url = product_data.get('url')
        if not url:
            return []

        try:
            response = self.session.get(url, timeout=30)
            if '<script id="__NEXT_DATA__"' not in response.text:
                self.command.stderr.write(self.command.style.ERROR("High-level block detected. Ending session."))
                # This will cause the run to fail and trigger cleanup
                raise InterruptedError("Session appears to be blocked.")

            response.raise_for_status()
            return [{'html': response.text, 'original_item': item}]

        except requests.exceptions.RequestException as e:
            self.command.stderr.write(self.command.style.ERROR(f"Request failed for {product_data.get('name')}: {e}"))
            return []


    def clean_raw_data(self, raw_data_list: list) -> dict:
        """
        Parses the HTML to find the barcode and returns the updated product data.
        """
        if not raw_data_list:
            return {}

        raw_data = raw_data_list[0]
        html = raw_data['html']
        original_item = raw_data['original_item']
        product_data = original_item['product']
        soup = BeautifulSoup(html, 'html.parser')

        gtin = None
        # Try ld+json first
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                    for item in items:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            gtin = item.get('gtin') or item.get('gtin13') or item.get('gtin14') or item.get('mpn')
                            if gtin: break
                    if gtin: break
                except json.JSONDecodeError:
                    continue

        # If not in ld+json, try __NEXT_DATA__
        if not gtin:
            json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
            if json_element and json_element.string:
                page_data = json.loads(json_element.string)
                product_json = page_data.get('pageProps', {}).get('product') or \
                               page_data.get('pageProps', {}).get('pdpLayout', {}).get('product')
                if product_json:
                    gtin = product_json.get('gtin')

        normalizer = ProductNormalizer({'barcode': str(gtin) if gtin else None})
        cleaned_barcode = normalizer.get_cleaned_barcode()

        if cleaned_barcode:
            product_data['barcode'] = cleaned_barcode
        else:
            product_data['barcode'] = None # Mark as processed

        # We return the full original item structure, but with the updated product data
        original_item['product'] = product_data
        return {'products': [original_item['product']], 'metadata': original_item.get('metadata')}


    def run(self):
        """
        Orchestrates the barcode enrichment process. Overrides the base method
        to handle session restarts.
        """
        while True:
            scrape_successful = False
            try:
                self.setup()
                self.jsonl_writer.open()
                work_items = self.get_work_items()
                self.output.update_progress(total_categories=len(work_items))

                for i, item in enumerate(work_items):
                    self.output.update_progress(categories_scraped=i + 1)
                    try:
                        raw_data_list = self.fetch_data_for_item(item)
                        if not raw_data_list:
                            # Write original data back if fetch fails
                            self.write_data({'products': [item['product']], 'metadata': item.get('metadata')})
                            continue

                        cleaned_data_packet = self.clean_raw_data(raw_data_list)
                        self.write_data(cleaned_data_packet)

                        # Write to progress file immediately after successful processing
                        with open(self.progress_file_path, 'a') as progress_f:
                            # The cleaned_data_packet has the updated product info
                            updated_line_data = {
                                'product': cleaned_data_packet['products'][0],
                                'metadata': cleaned_data_packet['metadata']
                            }
                            progress_f.write(json.dumps(updated_line_data) + '\n')

                    except InterruptedError:
                        self.command.stderr.write(self.command.style.ERROR("Session interrupted. Attempting to restart..."))
                        raise # Re-raise to be caught by the outer loop

                scrape_successful = True
                break # Exit the while loop on success

            except InterruptedError:
                self.jsonl_writer.cleanup() # Clean up partial file from the failed session
                self.command.stdout.write("--------------------------------------------------")
                # Loop will continue, causing a session restart
                continue
            finally:
                if self.jsonl_writer and self.jsonl_writer.is_open():
                    self.jsonl_writer.close()
                    if scrape_successful:
                        self.post_scrape_enrichment()
                        self.jsonl_writer.commit()
                        # Clean up progress file on full success
                        if os.path.exists(self.progress_file_path):
                            os.remove(self.progress_file_path)
                    else:
                        # Don't cleanup the main jsonl file, but progress file is kept
                        self.jsonl_writer.cleanup()
                if self.output:
                    self.output.finalize()

    def post_scrape_enrichment(self):
        """
        The primary purpose of this scraper is enrichment, so this is a no-op.
        The enriched file is already created. We just need to inform the user.
        """
        self.command.stdout.write(self.command.style.SUCCESS(
            f"Barcode enrichment complete. Final file at: {self.jsonl_writer.final_file_path}"
        ))
