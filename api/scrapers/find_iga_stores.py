import requests
import json
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_store_data_iga import clean_raw_store_data_iga
from api.utils.shop_scraping_utils.iga import (
    is_in_excluded_range,
    load_progress,
    parse_and_clean_stores,
    print_progress,
    save_progress,
    )

# --- CONFIGURATION ---
PROGRESS_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_iga\iga_stores_progress.json'
MAX_STORE_ID = 23001
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'

def find_iga_stores():
    """Fetches all store locations, skipping excluded ranges and saving progress."""
    start_id = load_progress(PROGRESS_FILE) + 1

    print("Performing thorough search for stores...")
    try:
        for store_id in range(start_id, MAX_STORE_ID + 1):
            if is_in_excluded_range(store_id):
                print_progress(store_id, MAX_STORE_ID, 0, f"Skipping ID {store_id} (excluded).")
                continue

            print_progress(store_id, MAX_STORE_ID, 0, f"Checking ID: {store_id}...")
            url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id}"
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                jsonp_content = response.text
                start_index = jsonp_content.find('(')
                end_index = jsonp_content.rfind(')')

                if start_index != -1 and end_index != -1:
                    json_str = jsonp_content[start_index + 1:end_index]
                    data = json.loads(json_str)
                    html_content = data.get('content', '')
                    new_stores = parse_and_clean_stores(html_content)

                    for store in new_stores:
                        cleaned_data = clean_raw_store_data_iga(store, "iga", datetime.now())
                        store_id = cleaned_data['store_data']['store_id']
                        filename = os.path.join(DISCOVERED_STORES_DIR, f"iga_{store_id}.json")
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(cleaned_data, f, indent=4)
                        print_progress(store_id, MAX_STORE_ID, 0, f"Saved store {store_id} to {filename}")

            except requests.exceptions.RequestException:
                pass # Ignore network errors silently
            except json.JSONDecodeError:
                pass # Ignore malformed JSON silently
            except ValueError:
                pass # Ignore other parsing errors
            
            save_progress(PROGRESS_FILE, store_id)

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Progress has been saved.")
    finally:
        print(f"\nFinished.")
        # Optionally remove progress file on natural completion
        if 'store_id' in locals() and store_id == MAX_STORE_ID:
             if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("Scraping complete. Progress file removed.")