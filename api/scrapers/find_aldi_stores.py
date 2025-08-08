
import json
import time
import os
import requests
from api.utils.shop_scraping_utils.aldi import (
    drange,
    load_existing_stores,
    load_progress,
    organize_aldi_stores,
    print_progress_bar,
    save_progress,
    save_stores_incrementally,
)

# --- CONFIGURATION ---
ALDI_API_URL = "https://api.aldi.com.au/v2/service-points"
OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_aldi\\aldi_stores_raw.json"
PROGRESS_FILE = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_aldi\\find_aldi_stores_progress.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -44.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0
LAT_STEP = 0.5
LON_STEP = 0.5

REQUEST_DELAY = 0.5

# --- MAIN SCRAPING LOGIC ---

def find_aldi_stores():
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
            all_stores = load_existing_stores(OUTPUT_FILE)
            start_lat, start_lon = load_progress(PROGRESS_FILE, LAT_MIN, LAT_STEP, LON_MIN, LON_MAX, LON_STEP)

            print("\nStarting ALDI store data scraping...")

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
                    
                    params = {
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "serviceType": "walk-in",
                        "includeNearbyServicePoints": "true",
                    }

                    try:
                        response = session.get(ALDI_API_URL, params=params, timeout=60)
                        response.raise_for_status()
                        data = response.json()

                        if "data" in data:
                            for store_details in data["data"]:
                                store_id = store_details.get('id')
                                if store_id and store_id not in all_stores:
                                    all_stores[store_id] = store_details
                                    save_stores_incrementally(OUTPUT_FILE, all_stores)

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
            
            print_progress_bar(total_steps, total_steps, LAT_MAX, LON_MAX, len(all_stores))
            print(f"\n\nFinished ALDI store scraping. Found {len(all_stores)} unique stores.")
            print(f"Raw data saved to {OUTPUT_FILE}")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)

            organize_aldi_stores()
            
            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
