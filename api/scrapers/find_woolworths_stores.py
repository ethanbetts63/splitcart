import json
import time
import os
import requests
from datetime import datetime
from api.utils.shop_scraping_utils.woolworths.clean_raw_store_data_woolworths import clean_raw_store_data_woolworths
from api.utils.shop_scraping_utils.woolworths import (
    drange,
    load_progress,
    print_progress_bar,
    save_progress,
)

# --- CONFIGURATION ---
WOOLWORTHS_API_URL = "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores"
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
PROGRESS_FILE = r"C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\find_woolworths_stores_progress.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -42.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0
LAT_STEP = 1
LON_STEP = 2

REQUEST_DELAY = 0.5

# --- MAIN SCRAPING LOGIC ---

def find_woolworths_stores():
    """Main function to drive the scraping process."""
    total_lat_steps = int((LAT_MAX - LAT_MIN) / LAT_STEP) + 1
    total_lon_steps = int((LON_MAX - LON_MIN) / LON_STEP) + 1
    total_steps = total_lat_steps * total_lon_steps

    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    while True:
        try:
            start_lat, start_lon = load_progress(PROGRESS_FILE, LAT_MIN, LAT_STEP, LON_MIN, LON_MAX, LON_STEP)
            found_stores = 0

            print("\nStarting Woolworths store data scraping...")

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
                                filename = os.path.join(DISCOVERED_STORES_DIR, f"woolworths_{store_id}.json")
                                if not os.path.exists(filename):
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(cleaned_data, f, indent=4)
                                    print(f"\nSaved store {store_id} to {filename}")
                                    found_stores += 1


                    except requests.exceptions.RequestException as e:
                        print(f"Request failed: {e}")
                        print("Restarting scraper in 10 seconds...")
                        time.sleep(10)
                        raise e # Reraise to trigger the restart
                    except json.JSONDecodeError:
                        print("Failed to decode JSON. Retrying...")
                        time.sleep(5)
                        continue
                    
                    save_progress(PROGRESS_FILE, current_lat, current_lon)
                    current_lon += LON_STEP
                    completed_steps += 1

                start_lon = LON_MIN
                current_lat += LAT_STEP
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX, found_stores)
            print(f"\n\nFinished Woolworths store scraping.")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            
            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
