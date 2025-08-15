import json
import time
import os
import requests
from datetime import datetime
from api.utils.shop_scraping_utils.woolworths.clean_raw_store_data_woolworths import clean_raw_store_data_woolworths
from api.utils.shop_scraping_utils.woolworths.drange import drange
from api.utils.shop_scraping_utils.woolworths.load_progress import load_progress
from api.utils.shop_scraping_utils.woolworths.print_progress_bar import print_progress_bar
from api.utils.shop_scraping_utils.woolworths.save_progress import save_progress

# --- CONFIGURATION ---
WOOLWORTHS_API_URL = "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores"
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
PROGRESS_FILE = r"C:\Users\ethan\coding\splitcart\api\data\archive\store_data\find_woolworths_stores_progress.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -42.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0

REQUEST_DELAY = 0.5

# --- MAIN SCRAPING LOGIC ---

def find_woolworths_stores():
    """Main function to drive the scraping process."""
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    # Set to track stores found in the current execution to avoid redundant file writes
    current_run_discovered_stores = set()

    while True:
        try:
            # Load progress or initialize new scraping parameters
            start_lat, start_lon, lat_step, lon_step, found_stores = load_progress(PROGRESS_FILE, LAT_MIN, LON_MIN)

            # Get the initial count of stores from the directory
            if found_stores == 0:
                 found_stores = len([name for name in os.listdir(DISCOVERED_STORES_DIR) if os.path.isfile(os.path.join(DISCOVERED_STORES_DIR, name)) and name.startswith('woolworths_')])

            print("\nStarting Woolworths store data scraping...")

            lat_steps = list(drange(LAT_MIN, LAT_MAX, lat_step))
            lon_steps = list(drange(LON_MIN, LON_MAX, lon_step))
            
            total_lat_steps = len(lat_steps)
            total_lon_steps = len(lon_steps)
            total_steps = total_lat_steps * total_lon_steps
            
            # Calculate initial completed_steps based on start_lat and start_lon
            completed_steps = 0
            try:
                start_lat_index = next(i for i, lat in enumerate(lat_steps) if abs(lat - start_lat) < 1e-9)
                completed_steps += start_lat_index * total_lon_steps
                start_lon_index = next(i for i, lon in enumerate(lon_steps) if abs(lon - start_lon) < 1e-9)
                completed_steps += start_lon_index
            except StopIteration:
                # If start_lat/start_lon not found, start from beginning
                completed_steps = 0


            current_lat = start_lat
            while current_lat <= LAT_MAX:
                current_lon = start_lon if current_lat == start_lat else LON_MIN
                while current_lon <= LON_MAX:
                    print_progress_bar(completed_steps, total_steps, current_lat, current_lon, found_stores)
                    
                    params = {
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "Max": 10000,
                        "Division": "SUPERMARKETS,EG,AMPOL",
                        "Facility": "",
                    }

                    try:
                        response = session.get(WOOLWORTHS_API_URL, params=params, timeout=60)
                        response.raise_for_status()
                        data = response.json()

                        if "Stores" in data:
                            for store_details in data["Stores"]:
                                cleaned_data = clean_raw_store_data_woolworths(store_details, "woolworths", datetime.now())
                                store_id = cleaned_data['store_data']['store_id']
                                
                                # Check if the store has already been found in this run
                                if store_id not in current_run_discovered_stores:
                                    filename = os.path.join(DISCOVERED_STORES_DIR, f"woolworths_{store_id}.json")
                                    if not os.path.exists(filename):
                                        with open(filename, 'w', encoding='utf-8') as f:
                                            json.dump(cleaned_data, f, indent=4)
                                        found_stores += 1
                                    current_run_discovered_stores.add(store_id)

                    except requests.exceptions.RequestException as e:
                        print(f"\nRequest failed: {e}")
                        raise e # Reraise to trigger the restart
                    except json.JSONDecodeError:
                        print("\nFailed to decode JSON. Retrying...")
                        time.sleep(5)
                        continue
                    
                    save_progress(PROGRESS_FILE, current_lat, current_lon, lat_step, lon_step, found_stores)
                    current_lon += lon_step
                    completed_steps += 1

                start_lon = LON_MIN # Reset for the next latitude sweep
                current_lat += lat_step
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX, found_stores)
            print(f"\n\nFinished Woolworths store scraping. Found {found_stores} unique stores.")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            
            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
