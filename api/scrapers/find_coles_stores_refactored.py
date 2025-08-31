import json
import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from api.utils.shop_scraping_utils.coles.clean_raw_store_data_coles import clean_raw_store_data_coles
from api.utils.shop_scraping_utils.coles.drange import drange
from api.utils.shop_scraping_utils.coles.get_graphql_query import get_graphql_query

# This refactored scraper intentionally mirrors the logic of the original
# find_coles_stores.py script closely, as the Coles API endpoint is sensitive.

class ColesStoreScraper:
    """A class to find Coles stores, wrapping the original, successful script logic."""
    COLES_API_URL = "https://www.coles.com.au/api/graphql"
    SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"
    OUTPUT_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
    PROGRESS_FILE = r"C:\Users\ethan\coding\splitcart\api\data\archive\store_data\find_coles_stores_progress.json"

    LAT_MIN = -44.0
    LAT_MAX = -10.0
    LON_MIN = 112.0
    LON_MAX = 154.0
    # Use fixed steps for reproducibility during a single run
    LAT_STEP = 0.5 
    LON_STEP = 0.5

    REQUEST_DELAY = 0.1

    def __init__(self, command):
        self.command = command
        self.stdout = command.stdout
        self.driver = None
        self.all_stores = {}
        self.found_stores_count = 0

    def load_existing_stores(self):
        """Loads store IDs from existing files in the discovered_stores directory."""
        existing_ids = set()
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
        for filename in os.listdir(self.OUTPUT_DIR):
            if filename.startswith('coles_') and filename.endswith('.json'):
                try:
                    store_id = filename.split('_')[1].split('.')[0]
                    existing_ids.add(store_id)
                except IndexError:
                    continue # Ignore malformed filenames
        return existing_ids

    def load_progress(self):
        """Loads progress from the progress file."""
        if os.path.exists(self.PROGRESS_FILE):
            try:
                with open(self.PROGRESS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                self.stdout.write("Could not read progress file, starting from scratch.")
        return {"lat": self.LAT_MIN, "lon": self.LON_MIN}

    def save_progress(self, lat, lon):
        """Saves progress to the progress file."""
        with open(self.PROGRESS_FILE, 'w') as f:
            json.dump({"lat": lat, "lon": lon}, f)

    def save_store(self, cleaned_data):
        """Saves a single cleaned store to a JSON file."""
        store_id = cleaned_data['store_data']['store_id']
        filename = os.path.join(self.OUTPUT_DIR, f"coles_{store_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4)
        self.found_stores_count += 1

    def run(self):
        """Main execution method."""
        try:
            self._execute_scraping_loop()
        except Exception as e:
            self.stdout.write(f"\n\nA critical error occurred: {e}")
            # The original script had a restart loop, which is handled by the command now.
            raise e # Re-raise to notify the caller
        finally:
            if self.driver:
                self.driver.quit()
                self.stdout.write("\nBrowser closed.")
            if os.path.exists(self.PROGRESS_FILE):
                os.remove(self.PROGRESS_FILE)
                self.stdout.write("Progress file removed.")

    def _execute_scraping_loop(self):
        """The main loop for iterating through coordinates and fetching data."""
        existing_store_ids = self.load_existing_stores()
        progress = self.load_progress()
        start_lat, start_lon = progress["lat"], progress["lon"]

        self.stdout.write("\n--- Launching Selenium browser to warm up session and make API calls ---")
        chrome_options = Options()
        chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_script_timeout(60)

        self.driver.get("https://www.coles.com.au")
        self.command.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
        input()
        self.driver.minimize_window()
        self.stdout.write("Starting Coles store data scraping...")

        lat_coords = list(drange(start_lat, self.LAT_MAX, self.LAT_STEP))
        lon_coords = list(drange(self.LON_MIN, self.LON_MAX, self.LON_STEP))
        total_steps = len(lat_coords) * len(lon_coords)
        completed_steps = 0

        for current_lat in lat_coords:
            # For the first latitude, start from the saved longitude, otherwise start from the beginning
            lon_iterator = drange(start_lon, self.LON_MAX, self.LON_STEP) if current_lat == start_lat else drange(self.LON_MIN, self.LON_MAX, self.LON_STEP)
            
            for current_lon in lon_iterator:
                self.command.stdout.write(f'\r{completed_steps}/{total_steps} | Found: {self.found_stores_count} | Coords: ({current_lat:.2f}, {current_lon:.2f})')
                self.stdout.flush()

                graphql_query = get_graphql_query(current_lat, current_lon)
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
                .then(response => response.ok ? response.json() : response.text().then(text => Promise.reject(new Error(f'HTTP error! status: ${{response.status}}, body: ${{text}}'))))
                .then(data => callback(JSON.stringify(data)))
                .catch(error => callback(JSON.stringify({{'error': error.toString()}})));
                '''
                
                json_response_str = self.driver.execute_async_script(js_code)
                data = json.loads(json_response_str)

                if "error" in data:
                    raise Exception(f"API Error: {data['error']}")

                if data.get("data") and data["data"].get("stores") and "results" in data["data"]["stores"]:
                    for result in data["data"]["stores"]["results"]:
                        store_details = result.get('store', {})
                        store_id = store_details.get('id')
                        if store_id and str(store_id) not in existing_store_ids:
                            cleaned_data = clean_raw_store_data_coles(store_details, "coles", datetime.now())
                            self.save_store(cleaned_data)
                            existing_store_ids.add(str(store_id))
                
                self.save_progress(current_lat, current_lon)
                time.sleep(self.REQUEST_DELAY)
                completed_steps += 1
            
            # After the first latitude row, the next longitude scan should start from the beginning
            start_lon = self.LON_MIN

        self.stdout.write(f"\n\nFinished Coles store scraping. Found {self.found_stores_count} new unique stores.")


def find_coles_stores(command):
    """Main function to drive the Coles store scraping process."""
    while True:
        try:
            scraper = ColesStoreScraper(command)
            scraper.run()
            break # Exit loop on success
        except Exception as e:
            command.stdout.write(f"\nScraper failed with error: {e}. Restarting in 10 seconds...")
            time.sleep(10)