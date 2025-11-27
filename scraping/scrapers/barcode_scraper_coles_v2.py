import os
import json
import requests
from bs4 import BeautifulSoup
from scraping.scrapers.base_product_scraper import BaseProductScraper
from scraping.utils.product_scraping_utils.jsonl_writer import JsonlWriter
from scraping.utils.product_scraping_utils.product_normalizer import ProductNormalizer
from data_management.utils.database_updating_utils.prefill_barcodes import prefill_barcodes_from_api
from scraping.utils.coles_session_manager import ColesSessionManager

class ColesBarcodeScraperV2(BaseProductScraper):
    """
    Refactored version of the barcode scraper that uses an external session manager.
    """

    def __init__(self, command, source_file_path: str, session_manager: ColesSessionManager, dev: bool = False):
        self.command = command
        self.source_file_path = source_file_path
        self.progress_file_path = source_file_path + ".progress"
        self.session = None  # Will be set in setup()
        self.session_manager = session_manager
        self.jsonl_writer = None
        self.output = None 
        self.dev = dev
        self.company = "coles"
        self.store_id = None
        self.store_name = None
        self.state = None

    def setup(self):
        """
        Initializes the scraper by setting up the output, loading metadata,
        and acquiring a session from the session manager.
        """
        try:
            with open(self.source_file_path, 'r') as f:
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
            return False

        # Acquire the session from the manager using the store_id from the file
        self.session = self.session_manager.get_session(self.store_id)

        # Essential to call super() to initialize self.output
        super().__init__(self.command, self.company, self.store_id, self.store_name, self.state)
        
        # We use a unique name for the output file to avoid clashes
        output_file_name = f"{self.store_name}-{self.store_id.split(':')[-1]}-barcodes"
        self.jsonl_writer = JsonlWriter(self.company, output_file_name, self.state)
        
        return True

    def get_work_items(self) -> list:
        found_products = {}
        if os.path.exists(self.progress_file_path):
            with open(self.progress_file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        sku = data.get('product', {}).get('sku')
                        if sku:
                            found_products[sku] = data
                    except json.JSONDecodeError:
                        continue

        try:
            with open(self.source_file_path, 'r') as f:
                master_line_list = [json.loads(line) for line in f if line.strip()]
        except (IOError, json.JSONDecodeError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"CRITICAL: Could not read source file: {e}"))
            return []

        master_product_list = [line.get('product') for line in master_line_list]
        enriched_master_list = prefill_barcodes_from_api(master_product_list, self.command, self.dev)
        for i, line_data in enumerate(master_line_list):
            if 'product' in line_data:
                line_data['product'] = enriched_master_list[i]

        lines_to_scrape = []
        for line_data in master_line_list:
            product_info = line_data.get('product', {})
            sku = product_info.get('sku')

            if sku in found_products:
                self.jsonl_writer.write_product(found_products[sku]['product'], found_products[sku].get('metadata', {}))
                continue

            if product_info.get('barcode') or not product_info.get('url') or product_info.get('has_no_coles_barcode'):
                self.jsonl_writer.write_product(product_info, line_data.get('metadata', {}))
                with open(self.progress_file_path, 'a') as progress_f:
                    progress_f.write(json.dumps(line_data) + '\n')
                continue

            lines_to_scrape.append(line_data)

        self.command.stdout.write(f"Found {len(lines_to_scrape)} products requiring barcode scraping.")
        return lines_to_scrape

    def fetch_data_for_item(self, item) -> list:
        product_data = item['product']
        url = product_data.get('url')
        if not url:
            return []

        response = self.session.get(url, timeout=30)
        
        if self.session_manager.is_blocked(response.text):
            self.command.stderr.write(self.command.style.ERROR("High-level block detected. Ending session."))
            raise InterruptedError("Session appears to be blocked by CAPTCHA.")

        response.raise_for_status()
        return [{'html': response.text, 'original_item': item}]

    def clean_raw_data(self, raw_data_list: list) -> dict:
        if not raw_data_list:
            return {}

        raw_data = raw_data_list[0]
        html = raw_data['html']
        original_item = raw_data['original_item']
        product_data = original_item['product']
        soup = BeautifulSoup(html, 'html.parser')

        gtin = None
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                    for item_ld in items:
                        if isinstance(item_ld, dict) and item_ld.get('@type') == 'Product':
                            gtin = item_ld.get('gtin') or item_ld.get('gtin13') or item_ld.get('gtin14') or item_ld.get('mpn')
                            if gtin: break
                    if gtin: break
                except json.JSONDecodeError:
                    continue

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
            product_data['barcode'] = None
            product_data['has_no_coles_barcode'] = True

        original_item['product'] = product_data
        
        # Write to progress file immediately after successful processing
        with open(self.progress_file_path, 'a') as progress_f:
            progress_f.write(json.dumps(original_item) + '\n')
            
        return {'products': [original_item['product']], 'metadata': original_item.get('metadata')}

    def run(self):
        """
        Overrides the base run method to handle the progress file cleanup.
        """
        super().run()
        # The base run method handles the main logic. We just need to clean up
        # the progress file if the scrape was successful.
        if os.path.exists(self.progress_file_path):
            os.remove(self.progress_file_path)
        # On full success, remove the original source file as it has been replaced
        if os.path.exists(self.source_file_path):
            os.remove(self.source_file_path)
