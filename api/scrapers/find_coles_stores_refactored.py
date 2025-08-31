
import json
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from api.scrapers.base_store_scraper import BaseStoreScraper
from api.utils.shop_scraping_utils.coles.clean_raw_store_data_coles import clean_raw_store_data_coles

class ColesStoreScraper(BaseStoreScraper):
    """
    A scraper for finding Coles stores by scanning a geographical grid.
    """
    COLES_API_URL = "https://www.coles.com.au/api/graphql"
    SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"

    # Geographical grid for Australia (approximate)
    LAT_MIN = -44.0
    LAT_MAX = -10.0
    LON_MIN = 112.0
    LON_MAX = 154.0
    LAT_STEP = random.uniform(0.25, 0.75)
    LON_STEP = random.uniform(0.25, 0.75)

    REQUEST_DELAY = 0.1

    def __init__(self, command):
        super().__init__(command, company='coles')

    def setup(self):
        """
        Launches a browser to warm up the session, then continues with requests.
        This is necessary to get past bot detection and obtain valid session cookies.
        """
        self.stdout.write("\n--- Launching Selenium browser to warm up session ---")
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            
            driver.get("https://www.coles.com.au")
            
            self.stdout.write("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
            input() # Pause for user to solve CAPTCHA

            # Transfer cookies from Selenium to the requests session
            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            self.stdout.write("Session cookies obtained. Closing browser and continuing with API calls.")

        except Exception as e:
            self.stdout.write(f"A critical error occurred during the Selenium phase: {e}\n")
            raise e
        finally:
            if driver:
                driver.quit()

    def get_work_items(self) -> list:
        """
        Generates a list of latitude and longitude coordinates to scan.
        """
        def drange(start, stop, step):
            r = start
            while r < stop:
                yield r
                r += step

        lat_steps = list(drange(self.LAT_MIN, self.LAT_MAX, self.LAT_STEP))
        lon_steps = list(drange(self.LON_MIN, self.LON_MAX, self.LON_STEP))
        
        return [(lat, lon) for lat in lat_steps for lon in lon_steps]

    def _get_graphql_query(self, latitude: float, longitude: float) -> dict:
        """Constructs the GraphQL query for a given coordinate."""
        return {
            "operationName": "getStores",
            "variables": {
                "latitude": latitude,
                "longitude": longitude,
                "radius": 50000,
                "brandIds": [1],
                "richQuery": None,
                "date": None,
                "time": None
            },
            "query": "query getStores($latitude: Float, $longitude: Float, $radius: Int, $brandIds: [Int], $richQuery: RichQuery, $date: String, $time: String) {\n  stores(latitude: $latitude, longitude: $longitude, radius: $radius, brandIds: $brandIds, richQuery: $richQuery, date: $date, time: $time) {\n    results {\n      ...storeSearchResult\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment storeSearchResult on StoreSearchResult {\n  store {\n    ...storeFields\n    __typename\n  }\n  distance\n  __typename\n}\n\nfragment storeFields on Store {\n  id\n  name\n  nickname\n  phoneNumber\n  location {\n    addressLine1\n    addressLine2\n    suburb\n    postcode\n    state\n    latitude\n    longitude\n    __typename\n  }\n  brand {\n    id\n    name\n    __typename\n  }\n  departments\n  tradingHours {\n    regular {\n      dayOfWeek\n      open\n      close\n      __typename\n    }\n    special {\n      date\n      open\n      close\n      __typename\n    }\n    __typename\n  }\n  features\n  __typename\n}\n"
        }

    def fetch_data_for_item(self, item: tuple) -> list:
        """
        Fetches store data for a given (latitude, longitude) coordinate pair.
        """
        latitude, longitude = item
        graphql_query = self._get_graphql_query(latitude, longitude)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Referer': 'https://www.coles.com.au/find-stores',
            'Origin': 'https://www.coles.com.au',
            'ocp-apim-subscription-key': self.SUBSCRIPTION_KEY
        }

        try:
            response = self.session.post(
                self.COLES_API_URL,
                headers=headers,
                json=graphql_query,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                self.stdout.write(f"GraphQL API Error: {data['errors']}")
                return []

            results = data.get("data", {}).get("stores", {}).get("results", [])
            time.sleep(self.REQUEST_DELAY)
            return results

        except (json.JSONDecodeError, Exception) as e:
            self.stdout.write(f"API request failed for coords ({latitude:.2f}, {longitude:.2f}): {e}")
            # Trigger the main error handling/restart loop in the base class
            raise e

    def clean_raw_data(self, raw_data: dict) -> dict:
        """
        Cleans the raw store data dictionary received from the API.
        """
        store_details = raw_data.get('store', {})
        return clean_raw_store_data_coles(store_details, self.company, datetime.now())

    def get_item_type(self) -> str:
        """Returns the type of the item being processed for progress display."""
        return "Coordinates"
