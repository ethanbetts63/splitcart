import os
import json
import time
from abc import ABC, abstractmethod

class BaseStoreScraper(ABC):
    """
    An abstract base class for company-specific store scrapers.
    """
    def __init__(self, command, company: str, progress_file_name: str = None):
        self.command = command
        self.company = company
        self.discovered_stores_dir = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
        if progress_file_name:
            self.progress_file = f"C:\\Users\\ethan\\coding\\splitcart\\api\\data\\archive\\store_data\\{progress_file_name}.json"
        else:
            self.progress_file = f"C:\\Users\\ethan\\coding\\splitcart\\api\\data\\archive\\store_data\\find_{self.company}_stores_progress.json"
        self.found_stores = 0
        self.stdout = command.stdout

    def run(self):
        """The main public method that orchestrates the entire scraping process."""
        self.setup()
        try:
            work_items = self.get_work_items()
            total_steps = len(work_items)
            completed_steps = self.load_progress()

            for i, item in enumerate(work_items[completed_steps:]):
                self.print_progress(completed_steps + i, total_steps, item)
                
                raw_data_list = self.fetch_data_for_item(item)

                self.save_progress(completed_steps + i)
                
                if not raw_data_list:
                    continue

                for raw_data in raw_data_list:
                    cleaned_data = self.clean_raw_data(raw_data)
                    self.save_store(cleaned_data)

            self.cleanup()
        except Exception as e:
            self.stdout.write(f"A critical error occurred: {e}")
            self.stdout.write("Restarting scraper in 10 seconds...")
            time.sleep(10)
            self.run()

    def save_store(self, cleaned_data):
        """Saves a single cleaned store to a JSON file."""
        store_id = cleaned_data['store_data']['store_id']
        
        # Sanitize the store_id for use in a filename by replacing colons
        safe_store_id = str(store_id).replace(':', '_')

        filename = os.path.join(self.discovered_stores_dir, f"{self.company}_{safe_store_id}.json")
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=4)
            self.found_stores += 1

    def load_progress(self):
        """Loads the last completed step from a progress file."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    return progress.get('completed_steps', 0)
            except (json.JSONDecodeError, IOError):
                self.stdout.write(f"\nWarning: {self.progress_file} is corrupted or unreadable. Starting from the beginning.")
        return 0

    def save_progress(self, completed_steps):
        """Saves the last completed step to a progress file."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump({'completed_steps': completed_steps}, f)

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
