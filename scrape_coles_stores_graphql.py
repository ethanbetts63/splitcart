import requests
import json
import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
COLES_API_URL = "https://www.coles.com.au/api/graphql"
SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"
OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\coles_graphql_raw_output.jsonl"
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
    """Loads the last processed coordinates from a file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                # Return the coordinates for the *next* step to start from
                return progress.get('last_lat', LAT_MIN), progress.get('last_lon', LON_MIN) + LON_STEP
        except (json.JSONDecodeError, IOError):
            print(f"Warning: {PROGRESS_FILE} is corrupted or unreadable. Starting from the beginning.")
    return LAT_MIN, LON_MIN

def save_raw_response(response_str):
    """Appends a single raw JSON response string to the output file."""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(response_str + '\n')

def get_graphql_query(latitude, longitude):
    """Returns the GraphQL query payload."""
    return {
        "operationName": "GetStores",
        "variables": {
            "brandIds": ["COL", "LQR", "VIN"],
            "latitude": latitude,
            "longitude": longitude
        },
        "query": "query GetStores($brandIds: [BrandId!], $latitude: Float!, $longitude: Float!) {\n  stores(brandIds: $brandIds, latitude: $latitude, longitude: $longitude) {\n    results {\n      distance\n      store {\n        id\n        name\n        address {\n          state\n          suburb\n          addressLine\n          postcode\n        }\n        position {\n          latitude\n          longitude\n        }\n        brand {\n          name\n          storeFinderId\n          id\n        }\n        phone\n        isTrading\n        services {\n          name\n          __typename\n        }\n        hours {\n          today {\n            time\n            holidayReason\n            isOpen\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"
    }

def print_progress_bar(iteration, total, lat, lon):
    """Displays a detailed progress bar."""
    percentage = 100 * (iteration / total)
    bar_length = 50
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% Complete ({iteration}/{total}) - Current Coords: ({lat:.2f}, {lon:.2f})')
    sys.stdout.flush()

# --- MAIN SCRAPING LOGIC ---

def fetch_coles_stores_graphql():
    """Main function to drive the scraping process."""
    driver = None
    # Calculate total steps for the progress bar
    total_lat_steps = int((LAT_MAX - LAT_MIN) / LAT_STEP) + 1
    total_lon_steps = int((LON_MAX - LON_MIN) / LON_STEP) + 1
    total_steps = total_lat_steps * total_lon_steps

    while True:
        try:
            start_lat, start_lon = load_progress()
            print("\n--- Launching Selenium browser to warm up session and make API calls ---")
            chrome_options = Options()
            chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.set_script_timeout(60)

            driver.get("https://www.coles.com.au")
            input("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
            print("\nStarting Coles store data scraping...")

            # Initialize progress tracking
            lat_steps = list(drange(LAT_MIN, LAT_MAX, LAT_STEP))
            lon_steps = list(drange(LON_MIN, LON_MAX, LON_STEP))
            
            # Recalculate completed steps if resuming
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
                    print_progress_bar(completed_steps, total_steps, current_lat, current_lon)
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
                    .then(response => {{
                        if (!response.ok) {{
                            return response.text().then(text => {{ 
                                throw new Error(`HTTP error! status: ${{response.status}}, body: ${{text}}`);
                            }});
                        }}
                        return response.json();
                    }})
                    .then(data => callback(JSON.stringify(data)))
                    .catch(error => callback(JSON.stringify({{'error': error.toString()}})));
                    '''
                    
                    try:
                        json_response_str = driver.execute_async_script(js_code)
                        data = json.loads(json_response_str)
                        if "error" in data:
                            print(f"\nAPI Error for Lat: {{current_lat:.2f}}, Lon: {{current_lon:.2f}}: {{data['error']}}")
                        else:
                            save_raw_response(json_response_str)

                    except Exception as e:
                        print(f"\nAn error occurred while fetching data for Lat: {{current_lat:.2f}}, Lon: {{current_lon:.2f}}: {{e}}")
                    
                    time.sleep(REQUEST_DELAY)
                    current_lon += LON_STEP
                    completed_steps += 1
                
                save_progress(current_lat, current_lon - LON_STEP) # Save progress at the end of a latitude row
                start_lon = LON_MIN # Reset for the next row
                current_lat += LAT_STEP
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX) # Final update to show 100%
            print(f"\n\nFinished Coles store scraping. Raw data appended to {{OUTPUT_FILE}}")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            break

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
        
        finally:
            if driver:
                driver.quit()
                print("\nBrowser closed.")

# Helper for floating point ranges
def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step

if __name__ == "__main__":
    fetch_coles_stores_graphql()