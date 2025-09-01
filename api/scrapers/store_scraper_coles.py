import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.clean_raw_store_data_coles import clean_raw_store_data_coles
from api.utils.shop_scraping_utils.drange import drange
from api.utils.shop_scraping_utils.get_graphql_query import get_graphql_query

class StoreScraperColes(BaseStoreScraper):
    """A class to find Coles stores, wrapping the original, successful script logic."""
    COLES_API_URL = "https://www.coles.com.au/api/graphql"
    SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"

    # Use fixed steps for reproducibility during a single run
    LAT_MIN, LAT_MAX, LAT_STEP = -44.0, -10.0, 0.5
    LON_MIN, LON_MAX, LON_STEP = 112.0, 154.0, 0.5

    REQUEST_DELAY = 0.1

    def __init__(self, command):
        super().__init__(command, 'coles')
        self.driver = None
        self.all_stores = {}

    # --- Override base class methods to implement the original script's logic ---

    def setup(self):
        """Initializes the Selenium driver and warms up the session."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.stdout.write("\n--- Launching Selenium browser to warm up session and make API calls ---")
        chrome_options = Options()
        chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_script_timeout(120) # Increased timeout for potentially slow network

        self.driver.get("https://www.coles.com.au")
        
        self.command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser.\n")
        self.command.stdout.write("Waiting for page to load completely (__NEXT_DATA__ script to appear)...")

        try:
            WebDriverWait(self.driver, 300, poll_frequency=2).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
            self.stdout.write("Page loaded successfully. Starting Coles store data scraping...")
        except Exception:
            self.stdout.write("Could not detect __NEXT_DATA__ script. The scraper may fail.")
            self.stdout.write("Press Enter to continue anyway...")
            input()

    def get_work_items(self) -> list:
        """Generates the grid of coordinates to scan."""
        lat_coords = list(drange(self.LAT_MIN, self.LAT_MAX, self.LAT_STEP))
        lon_coords = list(drange(self.LON_MIN, self.LON_MAX, self.LON_STEP))
        return [(lat, lon) for lat in lat_coords for lon in lon_coords]

    def fetch_data_for_item(self, item: tuple) -> list:
        """Executes a JavaScript fetch request within the browser to get store data."""
        latitude, longitude = item
        graphql_query = get_graphql_query(latitude, longitude)

        js_code = f'''
        const callback = arguments[arguments.length - 1];
        fetch('{self.COLES_API_URL}', {{
            method: 'POST',
            credentials: 'include',
            headers: {{
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Referer': 'https://www.coles.com.au/find-stores',
                'Origin': 'https://www.coles.com.au',
                'ocp-apim-subscription-key': '{self.SUBSCRIPTION_KEY}'
            }},
            body: JSON.stringify({json.dumps(graphql_query)})
        }})
        .then(response => response.ok ? response.json() : response.text().then(text => Promise.reject(new Error(`HTTP error! status: ${{response.status}}, body: ${{text}}`))))
        .then(data => callback(JSON.stringify(data)))
        .catch(error => callback(JSON.stringify({{'error': error.toString()}})));
        '''
        
        try:
            json_response_str = self.driver.execute_async_script(js_code)
            data = json.loads(json_response_str)

            if "error" in data:
                raise Exception(f"API Error: {data['error']}")

            return data.get("data", {}).get("stores", {}).get("results", [])
        except Exception as e:
            self.stdout.write(f"API request failed for coords ({latitude:.2f}, {longitude:.2f}): {e}")
            raise e # Re-raise to be caught by the main loop

    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw store data dictionary from the API."""
        store_details = raw_data.get('store', {})
        return clean_raw_store_data_coles(store_details, self.company, datetime.now())

    def cleanup(self):
        """Removes the progress file on successful completion."""
        # The driver is now closed in the finally block of run()
        super().cleanup()

    def get_item_type(self) -> str:
        return "Coordinates"

    # --- Main execution loop, overriding the base class's run() method ---

    def run(self):
        """Main execution method, faithfully replicating the original script's loop."""
        self.setup()
        success = False
        try:
            work_items = self.get_work_items()
            total_steps = len(work_items)
            
            start_step = self.load_progress()

            for i, item in enumerate(work_items[start_step:]):
                current_step = start_step + i
                self.print_progress(current_step, total_steps, item)

                results = self.fetch_data_for_item(item)
                
                if not results:
                    time.sleep(self.REQUEST_DELAY)
                    continue

                for result in results:
                    cleaned_data = self.clean_raw_data(result)
                    self.save_store(cleaned_data)
                
                self.save_progress(current_step + 1)
                time.sleep(self.REQUEST_DELAY)
            
            success = True # Mark as successful only if the loop completes

        except Exception as e:
            self.stdout.write(f"\n\nA critical error occurred: {e}")
            raise e # Re-raise to be handled by the restart loop
        finally:
            if success:
                self.cleanup()
            if self.driver:
                self.driver.quit()
                self.stdout.write("\nBrowser closed.")


def find_coles_stores(command):
    """Main function to drive the Coles store scraping process, with a restart loop."""
    while True:
        try:
            scraper = StoreScraperColes(command)
            scraper.run()
            command.stdout.write(command.style.SUCCESS("\n--- Coles store location scraping complete ---"))
            break # Exit loop on success
        except (Exception, KeyboardInterrupt) as e:
            command.stdout.write(f"\nScraper failed with error: {e} (repr: {repr(e)}). Restarting in 10 seconds...")
            time.sleep(10)