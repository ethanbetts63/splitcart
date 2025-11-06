import os
import json
from datetime import datetime
from django.conf import settings
from .atomic_scraping_utils import finalize_scrape

class JsonlWriter:
    def __init__(self, company: str, store_name_slug: str, state: str):
        self.temp_dir = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'temp_outbox')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Assign company and store_name_slug first
        self.company = company
        self.store_name_slug = store_name_slug
        self.state = state

        # Now use them to construct temp_file_path
        date_str = datetime.now().strftime('%Y-%m-%d')
        self.temp_file_path = os.path.join(self.temp_dir, f"{self.company.lower()}-{self.store_name_slug.lower()}-{date_str}.jsonl")
        
        self.final_outbox_path = os.path.join(settings.BASE_DIR, 'data_management', 'data', 'outboxes', 'product_outbox')
        self.temp_file_handle = None
        self.seen_product_keys = set()

    def open(self):
        """Opens the  JSONL file for writing."""
        self.temp_file_handle = open(self.temp_file_path, 'a', encoding='utf-8')

    def write_product(self, product_data: dict, metadata: dict) -> bool:
        """
        Writes a single product to the JSONL file, with in-scrape deduplication.
        Returns True if the product was written, False otherwise (e.g., if duplicate).
        """
        if not self.temp_file_handle:
            # print("Error: JSONL file not open. Call .open() first.")
            return False

        product_key = product_data.get('normalized_name_brand_size')
        if product_key and product_key not in self.seen_product_keys:
            try:
                json.dump({"product": product_data, "metadata": metadata}, self.temp_file_handle)
                self.temp_file_handle.write('\n')
                self.seen_product_keys.add(product_key)
                return True
            except Exception as e:
                # print(f"Error writing product to JSONL: {e}")
                return False
        return False # Product was a duplicate or missing key

    def close(self):
        """Closes the file handle if it's open."""
        if self.temp_file_handle:
            self.temp_file_handle.close()
            self.temp_file_handle = None

    def commit(self):
        """Moves the temporary file to the final inbox directory."""
        if os.path.exists(self.temp_file_path):
            final_file_name = os.path.basename(self.temp_file_path)
            finalize_scrape(self.temp_file_path, self.final_outbox_path, final_file_name)

    def cleanup(self):
        """Closes and removes the temporary file."""
        print(f"--- Cleanup called for {self.temp_file_path} ---")
        self.close()
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def finalize(self, scrape_successful: bool):
        """
        Finalizes the scrape by moving the file to inbox or deleting it.
        Maintained for backward compatibility.
        """
        if scrape_successful:
            self.close()
            self.commit()
        else:
            self.cleanup()
