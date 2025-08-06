import requests
import json
import html
import re
import os
import sys
from organize_iga_stores import organize_iga_stores

# --- CONFIGURATION ---
STORES_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\iga_stores_cleaned.json'
PROGRESS_FILE = 'C:\\Users\\ethan\\coding\\splitcart\\iga_stores_progress.json'
MAX_STORE_ID = 23001

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

def load_existing_stores():
    """Loads existing stores from the output file to avoid duplicates."""
    if os.path.exists(STORES_FILE):
        try:
            with open(STORES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: {STORES_FILE} is corrupted or has an unexpected format. Starting fresh.")
    return []

def parse_and_clean_stores(html_content):
    """Parses store data from HTML and returns a cleaned list of store dictionaries."""
    stores = []
    store_data_matches = re.findall(r'data-storedata="([^"]+)"', html_content)
    for store_data_str in store_data_matches:
        decoded_str = html.unescape(store_data_str)
        try:
            store_data = json.loads(decoded_str)
            # Clean the dictionary by removing the 'distance' key
            if 'distance' in store_data:
                del store_data['distance']
            stores.append(store_data)
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON: {e}")
            print(f"Problematic string: {decoded_str}")
    return stores

def print_progress(current_id, total_ids, found_count, message=""):
    """Displays a detailed, single-line progress bar."""
    percentage = 100 * (current_id / total_ids)
    bar_length = 30
    filled_length = int(bar_length * current_id // total_ids)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    # Pad the message to overwrite previous shorter messages
    status_message = message.ljust(40)
    sys.stdout.write(f'\rProgress: |{bar}| {percentage:.2f}% | Found: {found_count} | {status_message}')
    sys.stdout.flush()

# --- MAIN SCRAPING LOGIC ---

def fetch_all_stores_thorough():
    """Fetches all store locations, skipping excluded ranges and saving progress."""
    all_stores_data = load_existing_stores()
    existing_store_ids = {str(store['storeId']) for store in all_stores_data}
    start_id = load_progress() + 1

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
            
            save_progress(store_id)

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

if __name__ == "__main__":
    fetch_all_stores_thorough()
