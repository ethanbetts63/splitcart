import os
import json
import time
import requests
from abc import ABC, abstractmethod

from django.conf import settings

class BaseStoreScraper(ABC):
    """
    An abstract base class for company-specific store scrapers.
    """
    def __init__(self, command, company: str, progress_file_name: str = None):
        self.command = command
        self.company = company
        self.store_inbox_dir = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'outboxes', 'store_outbox')
        if progress_file_name:
            self.progress_file = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'temp_jsonl_store_storage', f"{progress_file_name}.json")
        else:
            self.progress_file = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'temp_jsonl_store_storage', f"find_{self.company}_stores_progress.json")
        self.found_stores = 0
        self.stdout = command.stdout
        self.processed_store_ids = set()

    def run(self):
        """The main public method that orchestrates the entire scraping process."""
        self.setup()
        MAX_RESTARTS = 3
        restarts = 0
        while True:
            try:
                work_items = self.get_work_items()
                total_steps = len(work_items)
                completed_steps = self.load_progress()
                consecutive_failures = 0
                MAX_FAILURES = 3

                for i, item in enumerate(work_items[completed_steps:]):
                    self.print_progress(completed_steps + i, total_steps, item)

                    raw_data_list = None
                    try:
                        raw_data_list = self.fetch_data_for_item(item)
                        consecutive_failures = 0  # Reset on success
                    except requests.exceptions.RequestException as e:
                        self.stdout.write(f"\nNetwork error: {e}")
                        consecutive_failures += 1
                        self.stdout.write(f"Consecutive network failures: {consecutive_failures}")
                        if consecutive_failures >= MAX_FAILURES:
                            self.stdout.write(f"\nStopping scraper due to {MAX_FAILURES} consecutive network failures.")
                            break

                    self.save_progress(completed_steps + i)

                    if not raw_data_list:
                        continue

                    for raw_data in raw_data_list:
                        cleaned_data = self.clean_raw_data(raw_data)
                        self.save_store(cleaned_data)

                self.cleanup()
                break
            except Exception as e:
                restarts += 1
                self.stdout.write(f"A critical error occurred: {e}")
                if restarts >= MAX_RESTARTS:
                    self.stdout.write(f"Stopping after {MAX_RESTARTS} critical errors.")
                    break
                self.stdout.write(f"Restarting scraper in 10 seconds... (attempt {restarts}/{MAX_RESTARTS})")
                time.sleep(10)


    def save_store(self, cleaned_data):
        """Saves a single cleaned store to a JSON file if not already processed in this session."""
        store_id = cleaned_data['store_data']['store_id']

        if store_id in self.processed_store_ids:
            return

        self.processed_store_ids.add(store_id)

        # Sanitize the store_id for use in a filename by replacing colons
        safe_store_id = str(store_id).replace(':', '_')

        filename = os.path.join(self.store_inbox_dir, f"{self.company}_{safe_store_id}.json")
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=4)
            self.found_stores += 1

    def load_progress(self):
        """Loads the last completed step and processed store IDs from a progress file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    self.processed_store_ids = set(progress.get('processed_store_ids', []))
                    return progress.get('completed_steps', 0)
            except (json.JSONDecodeError, IOError):
                self.stdout.write(f"\nWarning: {self.progress_file} is corrupted or unreadable. Starting from the beginning.")
        return 0

    def save_progress(self, completed_steps):
        """Saves the last completed step and processed store IDs to a progress file."""
        progress_data = {
            'completed_steps': completed_steps,
            'processed_store_ids': list(self.processed_store_ids)
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f)

    def cleanup(self):
        """Removes the progress file upon successful completion."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        self.stdout.write(f"\n\nFinished {self.company} store scraping. Found {self.found_stores} unique stores.")

    @abstractmethod
    def setup(self):
        """Perform any initial setup."""
        pass

    @abstractmethod
    def get_work_items(self) -> list:
        """Returns the list of items to scrape."""
        pass

    @abstractmethod
    def fetch_data_for_item(self, item) -> list:
        """Fetches the raw data for a single work item."""
        pass

    @abstractmethod
    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw store data."""
        pass

    def _format_item(self, item):
        if isinstance(item, tuple) and len(item) == 2:
            return f"({item[0]:.2f}, {item[1]:.2f})"
        return item

    def print_progress(self, iteration, total, item):
        """Prints the progress of the scraper."""
        item_type = self.get_item_type()
        formatted_item = self._format_item(item)
        self.stdout.write(f'{iteration}/{total} | [32mStores Found: {self.found_stores}[0m | [36m{item_type}: {formatted_item}[0m')
        self.stdout.flush()

    @abstractmethod
    def get_item_type(self) -> str:
        """Returns the type of the item being processed."""
        pass
