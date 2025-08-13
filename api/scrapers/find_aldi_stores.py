
import json
import time
import os
import requests
import random
from datetime import datetime
from api.utils.scraper_utils.clean_raw_store_data_aldi import clean_raw_store_data_aldi
from api.utils.shop_scraping_utils.aldi import (
    drange,
    load_progress,
    print_progress_bar,
    save_progress,
)

# --- CONFIGURATION ---
ALDI_API_URL = "https://api.aldi.com.au/v2/service-points"
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
PROGRESS_FILE = r"C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi\find_aldi_stores_progress.json"

# Geographical grid for Australia (approximate)
LAT_MIN = -44.0
LAT_MAX = -10.0
LON_MIN = 112.0
LON_MAX = 154.0
LAT_STEP = random.uniform(0.25, 0.75)
LON_STEP = random.uniform(0.25, 0.75)

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
            start_lat, start_lon = load_progress(PROGRESS_FILE, LAT_MIN, LAT_STEP, LON_MIN, LON_MAX, LON_STEP)
            found_stores = 0

            print("\nStarting ALDI store data scraping...")

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
                    print_progress_bar(completed_steps, total_steps, current_lat, current_lon, found_stores)
                    
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
                                cleaned_data = clean_raw_store_data_aldi(store_details, "aldi", datetime.now())
                                store_id = cleaned_data['store_data']['store_id']
                                filename = os.path.join(DISCOVERED_STORES_DIR, f"aldi_{store_id}.json")
                                if not os.path.exists(filename):
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(cleaned_data, f, indent=4)
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
            print(f"\n\nFinished ALDI store scraping. Found {found_stores} unique stores.")
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
            
            break # Exit the main while loop on success

        except Exception as e:
            print(f"\n\nA critical error occurred: {e}")
            print("Restarting scraper in 10 seconds...")
            time.sleep(10)
