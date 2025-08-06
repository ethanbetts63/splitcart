import requests
import json
import html
import re
import os

# --- CONFIGURATION ---
STORES_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\stores.json'
PROGRESS_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\fetch_thorough_progress.json'

# Ranges of store IDs to exclude from the search
EXCLUDED_RANGES = [
    (2115, 4350), (4357, 4370), (4397, 4410), (4418, 4434), (4552, 4587),
    (4641, 4662), (4666, 4686), (4724, 4799), (4801, 4833), (4874, 4911),
    (4916, 4931), (4962, 5023), (5031, 5050), (5063, 5091), (5335, 5393),
    (5481, 5537), (5540, 5558), (5581, 5868), (5870, 6211), (6213, 6530),
    (6532, 6610), (6644, 6678), (6680, 6772), (6774, 7158), (7165, 7311),
    (7316, 7404), (7408, 7433), (7434, 8291), (8293, 8360), (8364, 8420),
    (8422, 8455), (8479, 8627), (8628, 8817), (8820, 8859), (8866, 9067),
    (9070, 9167), (9482, 10817)
]

# --- UTILITY FUNCTIONS ---

def is_in_excluded_range(store_id):
    """Checks if a store ID is within any of the defined excluded ranges."""
    for start, end in EXCLUDED_RANGES:
        if start <= store_id <= end:
            return True
    return False

def save_progress(last_id):
    """Saves the last processed store ID to a file."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_id': last_id}, f)

def load_progress():
    """Loads the last processed store ID from a file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                last_id = progress.get('last_id', 0)
                print(f"Resuming from store ID: {last_id + 1}")
                return last_id
        except (json.JSONDecodeError, IOError):
            print(f"Warning: {PROGRESS_FILE} is corrupted. Starting from beginning.")
    return 0

def parse_stores_from_html(html_content):
    """Parses store data from the HTML content of an API response."""
    stores = []
    store_data_matches = re.findall(r'data-storedata="([^"]+)"', html_content)
    for store_data_str in store_data_matches:
        decoded_str = html.unescape(store_data_str)
        try:
            store_data = json.loads(decoded_str)
            stores.append(store_data)
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON: {e}")
            print(f"Problematic string: {decoded_str}")
    return stores

# --- MAIN SCRAPING LOGIC ---

def fetch_all_stores_thorough():
    """Fetches all store locations by iterating through a range of store IDs."""
    try:
        with open(STORES_FILE, 'r', encoding='utf-8') as f:
            all_stores_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_stores_data = []

    existing_store_ids = {store['storeId'] for store in all_stores_data}
    start_id = load_progress()

    print("Performing thorough search for stores...")
    for store_id in range(start_id, 23001):
        if is_in_excluded_range(store_id):
            print(f'\rSkipping ID {store_id} (in excluded range)...         ', end='')
            continue

        str_store_id = str(store_id)
        if str_store_id in existing_store_ids:
            print(f'\rSkipping ID {store_id} (already found)...            ', end='')
            continue

        print(f'\rChecking store ID: {store_id}...                         ', end='')
        url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            jsonp_content = response.text
            start_index = jsonp_content.find('(')
            end_index = jsonp_content.rfind(')')

            if start_index != -1 and end_index != -1:
                json_str = jsonp_content[start_index + 1:end_index]
                data = json.loads(json_str)
                html_content = data.get('content', '')
                new_stores = parse_stores_from_html(html_content)

                if not new_stores:
                    # This ID is likely valid but has no stores listed in its response HTML
                    pass
                else:
                    found_new = False
                    for store in new_stores:
                        if store['storeId'] not in existing_store_ids:
                            all_stores_data.append(store)
                            existing_store_ids.add(store['storeId'])
                            found_new = True
                            print(f"\nFound new store: {store['storeName']} ({store['storeId']}) from source ID {store_id}")
                    
                    if found_new:
                        # Save immediately after finding new stores
                        with open(STORES_FILE, 'w', encoding='utf-8') as f:
                            json.dump(all_stores_data, f, indent=4)
            else:
                # Handles cases where the response is not JSONP, but might be an error message
                pass # Ignore non-JSONP responses silently

        except requests.exceptions.RequestException as e:
            print(f"\nError fetching data for store ID {store_id}: {e}")
        except json.JSONDecodeError:
            # This can happen for IDs that don't exist, resulting in non-JSON response
            pass # Ignore these errors silently
        except ValueError as e:
            print(f"\nError processing response for store ID {store_id}: {e}")
        
        # Save progress after each attempt
        save_progress(store_id)

    # Final save and cleanup
    with open(STORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_stores_data, f, indent=4)
    
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    print(f"\n\nFinished. Found {len(all_stores_data)} total stores.")

if __name__ == "__main__":
    fetch_all_stores_thorough()