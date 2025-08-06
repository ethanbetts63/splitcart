import requests
import json
import os
from api.utils.shop_scraping_utils.iga import (
    is_in_excluded_range,
    load_existing_stores,
    load_progress,
    organize_iga_stores,
    parse_and_clean_stores,
    print_progress,
    save_progress,
    )

# --- CONFIGURATION ---
PROGRESS_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\iga_stores_progress.json'
MAX_STORE_ID = 23001
STORES_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\iga_stores_cleaned.json'

def find_iga_stores():
    """Fetches all store locations, skipping excluded ranges and saving progress."""
    all_stores_data = load_existing_stores(STORES_FILE)
    existing_store_ids = {str(store['storeId']) for store in all_stores_data}
    start_id = load_progress(PROGRESS_FILE) + 1

    print("Performing thorough search for stores...")
    try:
        for store_id in range(start_id, MAX_STORE_ID + 1):
            if is_in_excluded_range(store_id):
                print_progress(store_id, MAX_STORE_ID, len(existing_store_ids), f"Skipping ID {store_id} (excluded).")
                continue

            str_store_id = str(store_id)
            if str_store_id in existing_store_ids:
                print_progress(store_id, MAX_STORE_ID, len(existing_store_ids), f"Skipping ID {store_id} (found).")
                continue

            print_progress(store_id, MAX_STORE_ID, len(existing_store_ids), f"Checking ID: {store_id}...")
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

                    found_new_in_batch = False
                    for store in new_stores:
                        if str(store['storeId']) not in existing_store_ids:
                            all_stores_data.append(store)
                            existing_store_ids.add(str(store['storeId']))
                            found_new_in_batch = True
                    
                    if found_new_in_batch:
                        with open(STORES_FILE, 'w', encoding='utf-8') as f:
                            json.dump(all_stores_data, f, indent=4)
                        print_progress(store_id, MAX_STORE_ID, len(existing_store_ids), f"Processed {len(new_stores)} stores from ID {store_id}.")

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
        # Final save on exit
        with open(STORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_stores_data, f, indent=4)
        print(f"\nFinished. Found {len(all_stores_data)} total stores.")
        # Optionally remove progress file on natural completion
        if 'store_id' in locals() and store_id == MAX_STORE_ID:
             if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("Scraping complete. Progress file removed.")
             organize_iga_stores()
