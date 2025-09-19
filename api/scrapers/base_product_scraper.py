from abc import ABC, abstractmethod
from api.utils.scraper_utils.output_utils import ScraperOutput

class BaseProductScraper(ABC):
    """
    An abstract base class for company-specific scrapers.

    This class defines the overall scraping workflow and provides common
    functionality, while leaving company-specific implementation details to subclasses.
    """
    def __init__(self, command, company: str, store_id: str, store_name: str, state: str):
        self.command = command
        self.company = company
        self.store_id = store_id
        self.store_name = store_name
        self.state = state
        self.jsonl_writer = None
        self.output = ScraperOutput(self.command, self.company, self.store_name)

    def run(self):
        """The main public method that orchestrates the entire scraping process."""
        scrape_successful = False
        if not self.setup():
            return

        try:
            self.jsonl_writer.open()
            work_items = self.get_work_items()
            self.output.update_progress(total_categories=len(work_items))

            for i, item in enumerate(work_items):
                self.output.update_progress(categories_scraped=i + 1)
                raw_data_list = self.fetch_data_for_item(item)
                
                if not raw_data_list:
                    continue

                cleaned_data_packet = self.clean_raw_data(raw_data_list)
                self.write_data(cleaned_data_packet)
            
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

    # --- Methods to be implemented by subclasses ---

    @abstractmethod
    def setup(self):
        """
        Perform any initial setup, such as initializing the session,
        JsonlWriter, and any other class-specific attributes.
        """
        pass

    @abstractmethod
    def get_work_items(self) -> list:
        """Returns the list of categories, URLs, etc. to scrape."""
        pass

    @abstractmethod
    def fetch_data_for_item(self, item) -> list:
        """Fetches the raw data for a single work item."""
        pass

    @abstractmethod
    def clean_raw_data(self, raw_data: list) -> dict:
        """Calls the company-specific cleaning function."""
        pass

    # --- Optional hooks that can be overridden ---

    def post_scrape_enrichment(self):
        """Optional hook for post-scrape processing. Default is to do nothing."""
        pass
    
    def write_data(self, data_packet: dict):
        """Common logic for writing products to the jsonl file."""
        if data_packet.get('products'):
            new_products_count = 0
            duplicate_products_count = 0
            metadata_for_jsonl = data_packet.get('metadata', {})
            for product in data_packet['products']:
                if self.jsonl_writer.write_product(product, metadata_for_jsonl):
                    new_products_count += 1
                else:
                    duplicate_products_count += 1
            self.output.update_progress(new_products=new_products_count, duplicate_products=duplicate_products_count)
