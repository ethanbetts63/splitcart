import requests
import json
import os
from datetime import datetime
from api.utils.shop_scraping_utils.iga.clean_raw_store_data_iga import clean_raw_store_data_iga
from api.utils.shop_scraping_utils.iga.is_in_excluded_range import is_in_excluded_range
from api.utils.shop_scraping_utils.iga.load_progress import load_progress
from api.utils.shop_scraping_utils.iga.parse_and_clean_stores import parse_and_clean_stores
from api.utils.shop_scraping_utils.iga.print_progress import print_progress
from api.utils.shop_scraping_utils.iga.save_progress import save_progress

# --- CONFIGURATION ---
PROGRESS_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_iga\iga_stores_progress.json'
MAX_STORE_ID = 23001
DISCOVERED_STORES_DIR = r'C:\Users\ethan\coding\splitcart\api\data\discovered_stores'

def find_iga_stores():
    """Fetches all store locations, skipping excluded ranges and saving progress."""
    start_id = load_progress(PROGRESS_FILE) + 1
    found_stores_count = 0 # Initialize counter for stores found in this run

    print("Performing thorough search for stores...")
    try:
        for store_id_num in range(start_id, MAX_STORE_ID + 1):
            if is_in_excluded_range(store_id_num):
                print_progress(store_id_num, MAX_STORE_ID, 0, f"Skipping ID {store_id_num} (excluded).")
                continue

            print_progress(store_id_num, MAX_STORE_ID, 0, f"Checking ID: {store_id_num}...")
            url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id_num}"
            
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
                        # Only save if the file doesn't already exist to avoid overwriting and recount
                        if not os.path.exists(filename):
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(cleaned_data, f, indent=4)
                            found_stores_count += 1 

            except requests.exceptions.RequestException:
                pass # Ignore network errors silently
            except json.JSONDecodeError:
                pass # Ignore malformed JSON silently
            except ValueError:
                pass # Ignore other parsing errors
            
            save_progress(PROGRESS_FILE, store_id_num)
            print_progress(store_id_num, MAX_STORE_ID, found_stores_count, f"Checking ID: {store_id_num}...") # Update progress bar with actual count

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Progress has been saved.")
    finally:
        print(f"\nFinished. Total stores found and saved: {found_stores_count}") # Final print with total count
        # Optionally remove progress file on natural completion
        if 'store_id_num' in locals() and store_id_num == MAX_STORE_ID:
             if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("Scraping complete. Progress file removed.")