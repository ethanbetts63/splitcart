import json
import time
import os
import requests
from datetime import datetime
from api.utils.scraper_utils.clean_raw_store_data_woolworths import clean_raw_store_data_woolworths
from api.utils.shop_scraping_utils.woolworths import (
    print_progress_bar,
)

# --- CONFIGURATION ---
WOOLWORTHS_API_URL = "https://www.woolworths.com.au/api/v3/ui/fulfilment/stores"
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'
PROGRESS_FILE = r"C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\find_woolworths_stores2_progress.json"

# --- MAIN SCRAPING LOGIC ---

def find_woolworths_stores2():
    """Main function to drive the scraping process using postcodes."""
    
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    found_stores = 0
    
    print("\nStarting Woolworths store data scraping (postcode method)...")

    for postcode in range(1, 10000):
        print_progress_bar(postcode, 9999, 0, 0, found_stores)
        params = {
            "postcode": str(postcode).zfill(4)
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
            print(f"Request failed for postcode {postcode}: {e}")
            time.sleep(5)
            continue
        except json.JSONDecodeError:
            print(f"Failed to decode JSON for postcode {postcode}. Retrying...")
            time.sleep(5)
            continue

    print(f"\n\nFinished Woolworths store scraping. Found {found_stores} unique stores.")
