
import json
import random
from datetime import datetime
from api.scrapers.selenium_base_store_scraper import SeleniumBaseStoreScraper
from api.utils.shop_scraping_utils.coles.clean_raw_store_data_coles import clean_raw_store_data_coles

class ColesStoreScraper(SeleniumBaseStoreScraper):
    """
    A class to scrape Coles store data.
    """
    def __init__(self, command):
        super().__init__(command, 'coles')
        self.api_url = "https://www.coles.com.au/api/graphql"
        self.subscription_key = "eae83861d1cd4de6bb9cd8a2cd6f041e"
        self.lat_min = -44.0
        self.lat_max = -10.0
        self.lon_min = 112.0
        self.lon_max = 154.0
        self.lat_step = random.uniform(0.25, 0.75)
        self.lon_step = random.uniform(0.25, 0.75)

    def setup(self):
        """Initial setup for the Coles scraper."""
        self.stdout.write("\nStarting Coles store data scraping...")

    def get_warmup_url(self) -> str:
        return "https://www.coles.com.au"

    def get_work_items(self) -> list:
        """Generates a grid of coordinates to scrape."""
        lat_steps = list(self.drange(self.lat_min, self.lat_max, self.lat_step))
        lon_steps = list(self.drange(self.lon_min, self.lon_max, self.lon_step))
        return [(lat, lon) for lat in lat_steps for lon in lon_steps]

    def fetch_data_for_item(self, item) -> list:
        """Fetches store data for a given coordinate."""
        lat, lon = item
        graphql_query = self._get_graphql_query(lat, lon)
        js_code = f'''
        const callback = arguments[arguments.length - 1];
        fetch('{COLES_API_URL}', {{
            method: 'POST',
            credentials: 'include',
            headers: {{
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Referer': 'https://www.coles.com.au/find-stores',
                'Origin': 'https://www.coles.com.au',
                'ocp-apim-subscription-key': '{SUBSCRIPTION_KEY}'
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
            elif data.get("data") and data["data"].get("stores") and "results" in data["data"]["stores"]:
                return [result.get('store', {}) for result in data["data"]["stores"]["results"]]
        except Exception as e:
            self.stdout.write(f"An error occurred: {e}")
        return []

    def clean_raw_data(self, raw_data: dict) -> dict:
        """Cleans the raw Coles store data."""
        return clean_raw_store_data_coles(raw_data, self.company, datetime.now())

    def get_item_type(self) -> str:
        return "Coords"

    def _get_graphql_query(self, latitude, longitude):
        """Returns the GraphQL query payload."""
        return {
            "operationName": "GetStores",
            "variables": {
                "brandIds": ["COL", "LQR", "VIN"],
                "latitude": latitude,
                "longitude": longitude
            },
            "query": """query GetStores($brandIds: [BrandId!], $latitude: Float!, $longitude: Float!) {
  stores(brandIds: $brandIds, latitude: $latitude, longitude: $longitude) {
    results {
      store {
        id
        name
        address {
          state
          suburb
          addressLine
          postcode
        }
        position {
          latitude
          longitude
        }
        brand {
          name
          storeFinderId
          id
        }
        phone
        isTrading
        services {
          name
        }
      }
    }
  }
}"""
        }

    def drange(self, start, stop, step):
        r = start
        while r <= stop:
            yield r
            r += step


def find_coles_stores(command):
    """Main function to drive the Coles store scraping process."""
    scraper = ColesStoreScraper(command)
    scraper.run()
