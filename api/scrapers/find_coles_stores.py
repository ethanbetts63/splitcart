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
from api.utils.shop_scraping_utils.coles import (
    drange,
    get_graphql_query, 
    load_existing_stores,
    load_progress,
    print_progress_bar,
    save_progress,
    save_stores_incrementally,
    process_coles_stores_for_inbox
)

# --- CONFIGURATION ---
COLES_API_URL = "https://www.coles.com.au/api/graphql"
SUBSCRIPTION_KEY = "eae83861d1cd4de6bb9cd8a2cd6f041e"
OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_coles\\coles_stores_cleaned.json"
PROGRESS_FILE = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_coles\\find_coles_stores_progress.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -44.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0
LAT_STEP = random.uniform(0.25, 0.75)
LON_STEP = random.uniform(0.25, 0.75)

REQUEST_DELAY = 0.1 

# --- MAIN SCRAPING LOGIC ---

def find_coles_stores():
    """Main function to drive the scraping process."""
    driver = None
    total_lat_steps = int((LAT_MAX - LAT_MIN) / LAT_STEP) + 1
    total_lon_steps = int((LON_MAX - LON_MIN) / LON_STEP) + 1
    total_steps = total_lat_steps * total_lon_steps

    while True:
        try:
            all_stores = load_existing_stores(OUTPUT_FILE)
            start_lat, start_lon = load_progress(PROGRESS_FILE, LAT_MIN, LAT_STEP, LON_MIN, LON_MAX, LON_STEP)

            print("\n--- Launching Selenium browser to warm up session and make API calls ---")
            chrome_options = Options()
            chrome_options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
            driver.set_script_timeout(60)

            driver.get("https://www.coles.com.au")
            input("ACTION REQUIRED: Please solve any CAPTCHA in the browser, then press Enter here to continue...")
            driver.minimize_window() # Minimize the browser window
            print("Starting Coles store data scraping...")
            
            lat_steps = list(drange(LAT_MIN, LAT_MAX, LAT_STEP))
            lon_steps = list(drange(LON_MIN, LON_MAX, LON_STEP))
            
            # Calculate initial completed_steps based on start_lat and start_lon
            initial_completed_steps = 0
            # Find the index of start_lat in lat_steps
            # Use a small tolerance for floating point comparison
            start_lat_index = -1
            for i, lat_val in enumerate(lat_steps):
                if abs(lat_val - start_lat) < 1e-9: # Small tolerance
                    start_lat_index = i
                    break
            
            if start_lat_index != -1:
                initial_completed_steps += start_lat_index * len(lon_steps)
                
                # Find the index of start_lon in lon_steps
                start_lon_index = -1
                for i, lon_val in enumerate(lon_steps):
                    if abs(lon_val - start_lon) < 1e-9: # Small tolerance
                        start_lon_index = i
                        break
                
                if start_lon_index != -1:
                    initial_completed_steps += start_lon_index
            
            completed_steps = initial_completed_steps

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
                                    cleaned_data = clean_raw_store_data_coles(store_details, "coles", datetime.now())
                                    all_stores[store_id] = cleaned_data
                                    save_stores_incrementally(OUTPUT_FILE, all_stores)

                    except Exception as e:
                        # This will now catch the API error and trigger the restart
                        raise e
                    
                    save_progress(PROGRESS_FILE, current_lat, current_lon)
                    time.sleep(REQUEST_DELAY)
                    current_lon += LON_STEP
                    completed_steps += 1

                start_lon = LON_MIN
                current_lat += LAT_STEP
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX, len(all_stores))
            print(f"\n\nFinished Coles store scraping. Found {len(all_stores)} unique stores.")
            print(f"Cleaned data saved to {OUTPUT_FILE}")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            
            # Process and move data to inbox
            process_coles_stores_for_inbox()

            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
        
        finally:
            if driver:
                driver.quit()
                print("\nBrowser closed.")