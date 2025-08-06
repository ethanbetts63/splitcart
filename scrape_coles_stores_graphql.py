import requests
import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from organize_coles_stores import organize_coles_stores

# --- CONFIGURATION ---
COLES_API_URL = "https://www.coles.com.au/api/graphql"
SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"
OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\coles_stores_cleaned.json"
PROGRESS_FILE = "C:\\Users\\ethan\\coding\\splitcart\\coles_progress_graphql.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -44.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0
LAT_STEP = 0.5
LON_STEP = 0.5

REQUEST_DELAY = 0.5  # seconds between requests

# --- UTILITY FUNCTIONS ---

def save_progress(lat, lon):
    """Saves the last processed coordinates to a file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_lat': lat, 'last_lon': lon}, f)

def load_progress():
    """Loads the last processed coordinates from a file, handling rollover."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                last_lat = progress.get('last_lat', LAT_MIN)
                last_lon = progress.get('last_lon', LON_MIN)

                if last_lon >= LON_MAX:
                    print(f"\nCompleted row for Lat: {last_lat}. Resuming on next latitude.")
                    return last_lat + LAT_STEP, LON_MIN
                else:
                    print(f"\nResuming from Lat: {last_lat}, Lon: {last_lon + LON_STEP}")
                    return last_lat, last_lon + LON_STEP
        except (json.JSONDecodeError, IOError):
            print(f"\nWarning: {PROGRESS_FILE} is corrupted or unreadable. Starting from the beginning.")
    return LAT_MIN, LON_MIN

def load_existing_stores():
    """Loads existing stores from the output file to avoid duplicates."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                stores_list = json.load(f)
                return {store['id']: store for store in stores_list}
        except (json.JSONDecodeError, KeyError):
            print(f"\nWarning: {OUTPUT_FILE} is corrupted or has an unexpected format. Starting fresh.")
    return {}

def save_stores_incrementally(stores_dict):
    """Saves the dictionary of cleaned stores to the output file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(stores_dict.values()), f, indent=4)

def get_graphql_query(latitude, longitude):
    """Returns the GraphQL query payload."""
    return {
        "operationName": "GetStores",
        "variables": {
            "brandIds": ["COL", "LQR", "VIN"],
            "latitude": latitude,
            "longitude": longitude
        },
        "query": "query GetStores($brandIds: [BrandId!], $latitude: Float!, $longitude: Float!) {\n  stores(brandIds: $brandIds, latitude: $latitude, longitude: $longitude) {\n    results {\n      store {\n        id\n        name\n        address {\n          state\n          suburb\n          addressLine\n          postcode\n        }\n        position {\n          latitude\n          longitude\n        }\n        brand {\n          name\n          storeFinderId\n          id\n        }\n        phone\n        isTrading\n        services {\n          name\n        }\n      }\n    }\n  }\n}"
    }

def print_progress_bar(iteration, total, lat, lon, store_count):
    """Displays a detailed progress bar with store count."""
    percentage = 100 * (iteration / total)
    bar_length = 40
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% ({iteration}/{total}) | Stores Found: {store_count} | Coords: ({lat:.2f}, {lon:.2f})')
    sys.stdout.flush()

# --- MAIN SCRAPING LOGIC ---

def fetch_coles_stores_graphql():
    """Main function to drive the scraping process."""
    driver = None
    total_lat_steps = int((LAT_MAX - LAT_MIN) / LAT_STEP) + 1
    total_lon_steps = int((LON_MAX - LON_MIN) / LON_STEP) + 1
    total_steps = total_lat_steps * total_lon_steps

    all_stores = load_existing_stores()
    start_lat, start_lon = load_progress()

    while True:
        try:
            print("\n--- Launching Selenium browser to warm up session and make API calls ---")
            chrome_options = Options()
            chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.set_script_timeout(60)

            driver.get("https://www.coles.com.au")
            input("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
            print("\nStarting Coles store data scraping...")

            lat_steps = list(drange(LAT_MIN, LAT_MAX, LAT_STEP))
            lon_steps = list(drange(LON_MIN, LON_MAX, LON_STEP))
            
            completed_steps = 0
            if start_lat > LAT_MIN:
                completed_lat_steps = lat_steps.index(start_lat)
                completed_steps += completed_lat_steps * len(lon_steps)
            if start_lon > LON_MIN:
                completed_steps += lon_steps.index(start_lon)

            current_lat = start_lat
            while current_lat <= LAT_MAX:
                current_lon = start_lon if current_lat == start_lat else LON_MIN
                while current_lon <= LON_MAX:
                    print_progress_bar(completed_steps, total_steps, current_lat, current_lon, len(all_stores))
                    graphql_query = get_graphql_query(current_lat, current_lon)
                    
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
                        json_response_str = driver.execute_async_script(js_code)
                        data = json.loads(json_response_str)

                        if "error" in data:
                            raise Exception(f"API Error: {data['error']}") # Raise exception to trigger restart

                        elif data.get("data") and data["data"].get("stores") and "results" in data["data"]["stores"]:
                            for result in data["data"]["stores"]["results"]:
                                store_details = result.get('store', {})
                                store_id = store_details.get('id')
                                if store_id and store_id not in all_stores:
                                    cleaned_store = {
                                        "id": store_id,
                                        "name": store_details.get("name"),
                                        "phone": store_details.get("phone"),
                                        "isTrading": store_details.get("isTrading"),
                                        "address": store_details.get("address"),
                                        "position": store_details.get("position"),
                                        "brand": store_details.get("brand")
                                    }
                                    all_stores[store_id] = cleaned_store
                                    save_stores_incrementally(all_stores)

                    except Exception as e:
                        # This will now catch the API error and trigger the restart
                        raise e
                    
                    time.sleep(REQUEST_DELAY)
                    current_lon += LON_STEP
                    completed_steps += 1
                
                save_progress(current_lat, current_lon - LON_STEP)
                start_lon = LON_MIN
                current_lat += LAT_STEP
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX, len(all_stores))
            print(f"\n\nFinished Coles store scraping. Found {len(all_stores)} unique stores.")
            print(f"Cleaned data saved to {OUTPUT_FILE}")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            
            # Organize the final data
            organize_coles_stores()

            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
        
        finally:
            if driver:
                driver.quit()
                print("\nBrowser closed.")

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

if __name__ == "__main__":
    fetch_coles_stores_graphql()
