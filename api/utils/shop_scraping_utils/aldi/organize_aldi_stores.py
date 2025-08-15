import json
import os
from django.utils.text import slugify
import json
import os
from datetime import date

# --- CONFIGURATION ---
SOURCE_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi\aldi_stores_raw.json'
BASE_OUTPUT_DIR = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi'


def organize_aldi_stores():
    """Reads the raw stores file and organizes stores into state specific files with metadata."""
    print(f"Starting organization of {SOURCE_FILE}...")

    # 1. Read the source file
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            all_stores_dict = json.load(f)
            all_stores_list = list(all_stores_dict.values())
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}. Nothing to do.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {SOURCE_FILE}.")
        return

    # 2. Group stores by state
    grouped_stores = {}
    for store in all_stores_list:
        try:
            address = store.get('address', {})
            state_iso = address.get('regionIsoCode', 'unknown-state').lower()
            if not state_iso: # Add this check
                state_iso = 'unknown-state'
            state_name = address.get('regionName', 'Unknown State')

            if state_iso not in grouped_stores:
                grouped_stores[state_iso] = {'name': state_name, 'stores': []}
            
            grouped_stores[state_iso]['stores'].append(store)

        except Exception as e:
            print(f"Skipping store due to error: {e}\nProblematic store data: {store}")

    # 3. Write the grouped data to respective files with metadata
    if not os.path.exists(BASE_OUTPUT_DIR):
        print(f"Base output directory does not exist: {BASE_OUTPUT_DIR}")
        return

    today_date = date.today().isoformat()

    for state_iso, state_data in grouped_stores.items():
        output_filename = os.path.join(BASE_OUTPUT_DIR, f"{state_iso}.json")
        stores = state_data['stores']
        state_name = state_data['name']
        
        # Create the final data structure with metadata
        output_data = {
            "metadata": {
                "number_of_stores": len(stores),
                "company": "aldi",
                "state": state_name,
                "state_iso": state_iso.upper(),
                "date_scraped": today_date
            },
            "stores": stores
        }

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
            print(f"Wrote {len(stores)} stores to {output_filename}")
        except IOError as e:
            print(f"Error writing to file {output_filename}: {e}")

    # 4. Delete the original source file after successful processing
    try:
        os.remove(SOURCE_FILE)
        print(f"Successfully removed original file: {SOURCE_FILE}")
    except OSError as e:
        print(f"Error deleting source file: {e}")

    from api.utils.shop_scraping_utils.aldi.create_aldi_stores_by_state import create_aldi_stores_by_state

    print("\nOrganization complete.")
    create_aldi_stores_by_state()
