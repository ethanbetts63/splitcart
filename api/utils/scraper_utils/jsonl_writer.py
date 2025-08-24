import os
import json
from django.conf import settings
from .atomic_scraping_utils import finalize_scrape

class JsonlWriter:
    def __init__(self, company: str, store_name_slug: str, state: str):
        self.temp_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'temp_inbox')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        self.temp_file_path = os.path.join(self.temp_dir, f"{store_name_slug}.jsonl")
        self.inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')
        self.temp_file_handle = None
        self.seen_product_keys = set()
        self.company = company
        self.store_name_slug = store_name_slug
        self.state = state

    def open(self):
        """Opens the  JSONL file for writing."""
        print(f"Opening  JSONL file: {self.temp_file_path}")
        self.temp_file_handle = open(self.temp_file_path, 'a', encoding='utf-8')

    def write_product(self, product_data: dict, metadata: dict) -> bool:
        """
        Writes a single product to the JSONL file, with in-scrape deduplication.
        Returns True if the product was written, False otherwise (e.g., if duplicate).
        """
        if not self.temp_file_handle:
            print("Error: JSONL file not open. Call .open() first.")
            return False

        product_key = product_data.get('normalized_name_brand_size')
        if product_key and product_key not in self.seen_product_keys:
            try:
                json.dump({"product": product_data, "metadata": metadata}, self.temp_file_handle)
                self.temp_file_handle.write('\n')
                self.seen_product_keys.add(product_key)
                return True
            except Exception as e:
                print(f"Error writing product to JSONL: {e}")
                return False
        return False # Product was a duplicate or missing key

    def finalize(self, scrape_successful: bool):
        """
        Finalizes the scrape by moving the file to inbox or deleting it.
        Must be called in a finally block.
        """
        if self.temp_file_handle:
            self.temp_file_handle.close()
            self.temp_file_handle = None # Clear handle after closing

        if scrape_successful:
            print(f"Finalizing scrape for {self.store_name_slug}.")
            store_id = self.store_name_slug.split('-')[-1]
            final_file_name = f"{self.company.lower()}_{store_id.lower()}.jsonl"
            finalize_scrape(self.temp_file_path, self.inbox_path, final_file_name)
            print(f"Successfully moved file to inbox for {self.store_name_slug}.")
        else:
            if os.path.exists(self.temp_file_path):
                os.remove(self.temp_file_path)
            print(f"Scrape for {self.store_name_slug} failed. File removed.")
