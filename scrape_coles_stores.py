import requests
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Configuration
COLES_API_URL = "https://www.coles.com.au/api/bff/locations/search"
SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e" # Your identified subscription key
OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\coles_stores.json"
PROGRESS_FILE = "C:\\Users\\ethan\\coding\\splitcart\\coles_progress.json"

# Geographical grid for Australia (approximate)
# Adjust these ranges and steps for more or less coverage/density
LAT_MIN = -44.0 # Southern Tasmania
LAT_MAX = -10.0 # Northern Australia
LON_MIN = 112.0 # Western Australia
LON_MAX = 154.0 # Eastern Australia
LAT_STEP = 1.0 # Degrees
LON_STEP = 1.0 # Degrees

DISTANCE = 50 # km
NUMBER_OF_LOCATIONS = 20 # Max locations per request
REQUEST_DELAY = 0.5 # seconds between requests

def save_progress(lat, lon):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_lat': lat, 'last_lon': lon}, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                return progress.get('last_lat', LAT_MIN), progress.get('last_lon', LON_MIN)
        except json.JSONDecodeError:
            print(f"Warning: {PROGRESS_FILE} is corrupted. Starting from beginning.")
    return LAT_MIN, LON_MIN

def load_existing_stores():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                stores_list = json.load(f)
                return {store['storeId']: store for store in stores_list}
        except json.JSONDecodeError:
            print(f"Warning: {OUTPUT_FILE} is corrupted. Starting with empty store list.")
    return {}

def save_stores_incrementally(stores_dict):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(stores_dict.values()), f, indent=4)

def fetch_coles_stores():
    all_coles_stores = load_existing_stores()
    driver = None

    while True: # Outer loop for retries
        try:
            start_lat, start_lon = load_progress()
            print("\n--- Launching Selenium browser to warm up session and make API calls ---")
            chrome_options = Options()
            chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.set_script_timeout(60) # 60 seconds timeout for scripts

            driver.get("https://www.coles.com.au")

            input("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")

            print("\nStarting Coles store data scraping using Selenium browser...")

            current_lat = start_lat
            while current_lat <= LAT_MAX:
                current_lon = start_lon if current_lat == start_lat else LON_MIN # Reset longitude if new latitude
                while current_lon <= LON_MAX:
                    params = {
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "distance": DISTANCE,
                        "numberOfLocations": NUMBER_OF_LOCATIONS
                    }
                    api_url_with_params = f"{COLES_API_URL}?latitude={params['latitude']}&longitude={params['longitude']}&distance={params['distance']}&numberOfLocations={params['numberOfLocations']}"

                    js_code = f"""
                    return fetch('{api_url_with_params}', {{
                        method: 'GET',
                        headers: {{
                            'ocp-apim-subscription-key': '{SUBSCRIPTION_KEY}',
                            'Accept': 'application/json',
                            'User-Agent': 'SplitCartScraper/1.0 (Contact: admin@splitcart.com)',
                            'Referer': 'https://www.coles.com.au/'
                        }}
                    }})
                    .then(response => response.json())
                    .then(data => JSON.stringify(data))
                    .catch(error => JSON.stringify({{'error': error.message}}));
                    """
                    
                    print(f"Fetching stores for Lat: {current_lat:.2f}, Lon: {current_lon:.2f}")

                    try:
                        json_response_str = driver.execute_script(js_code)
                        data = json.loads(json_response_str)

                        if "error" in data:
                            raise requests.exceptions.RequestException(data["error"])

                        if "locations" in data:
                            for location in data["locations"]:
                                store_id = location.get("fulfillmentStore", {}).get("storeId")
                                if not store_id: # Fallback to locationId if fulfillmentStore.storeId is missing
                                    store_id = location.get("locationId")

                                if store_id and store_id not in all_coles_stores:
                                    store_info = {
                                        "storeId": store_id,
                                        "locationId": location.get("locationId"),
                                        "storeName": location.get("locationName", location.get("fulfillmentStore", {}).get("storeName")),
                                        "address": location.get("address"),
                                        "suburb": location.get("suburb"),
                                        "postcode": location.get("postcode"),
                                        "state": location.get("state"),
                                        "latitude": location.get("latitude"),
                                        "longitude": location.get("longitude"),
                                        "phone": location.get("phone"),
                                        "brandId": location.get("brandId"),
                                        "brandName": location.get("brandName"),
                                        "storeRestrictions": location.get("storeRestrictions"),
                                    }
                                    all_coles_stores[store_id] = store_info
                                    save_stores_incrementally(all_coles_stores) # Save immediately
                                    print(f"  Found new Coles store: {store_info['storeName']} ({store_id})")
                        
                    except Exception as e: # Catch all exceptions from execute_script and json.loads
                        print(f"Error fetching data for Lat: {current_lat:.2f}, Lon: {current_lon:.2f}: {e}")
                        break # Break inner loop to restart Selenium
                    
                    time.sleep(REQUEST_DELAY)
                    current_lon += LON_STEP
                
                save_progress(current_lat, current_lon) # Save progress after each longitude iteration
                current_lat += LAT_STEP
            
            # If we reached here, it means the entire grid was scraped successfully
            print(f"\nFinished Coles store scraping. Found {len(all_coles_stores)} unique stores.")
            print(f"Data saved to {OUTPUT_FILE}")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE) # Clean up progress file on successful completion
            break # Break outer loop on successful completion

        except Exception as e: # Catch critical errors that require restarting Selenium
            print(f"\nA critical error occurred, restarting scraper: {e}")
        
        finally:
            if driver:
                driver.quit()
                driver = None # Reset driver to None for the next iteration

if __name__ == "__main__":
    fetch_coles_stores()