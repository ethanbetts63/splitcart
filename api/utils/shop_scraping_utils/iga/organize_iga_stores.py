import json
import os
from datetime import date

# --- CONFIGURATION ---
SOURCE_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_iga\iga_stores_cleaned.json'
BASE_OUTPUT_DIR = 'C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_iga'

def organize_iga_stores():
    """Reads the cleaned IGA stores file and organizes stores into state-specific files with metadata."""
    print(f"\nStarting organization of {SOURCE_FILE}...")

    # 1. Read the source file
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            all_stores = json.load(f)
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}. Nothing to do.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {SOURCE_FILE}.")
        return

    # 2. Group stores by state
    grouped_stores = {}
    for store in all_stores:
        try:
            state = store.get('state', 'unknown-state').lower()
            if not state or not state.strip():
                state = 'unknown-state'
            if state not in grouped_stores:
                grouped_stores[state] = []
            grouped_stores[state].append(store)
        except Exception as e:
            print(f"Skipping store due to error: {e}\nProblematic store data: {store}")

    # 3. Write the grouped data to respective files with metadata
    if not os.path.exists(BASE_OUTPUT_DIR):
        print(f"Base output directory does not exist: {BASE_OUTPUT_DIR}")
        return

    today_date = date.today().isoformat()

    for state, stores in grouped_stores.items():
        output_filename = os.path.join(BASE_OUTPUT_DIR, f"{state}.json")
        
        output_data = {
            "metadata": {
                "number_of_stores": len(stores),
                "company": "iga",
                "state": state.upper(),
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

    print("\nIGA store organization complete.")

