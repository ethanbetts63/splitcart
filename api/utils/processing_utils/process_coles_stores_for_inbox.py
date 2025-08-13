import json
import os

def process_coles_stores_for_inbox():
    OUTPUT_FILE = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\store_data\\stores_coles\\coles_stores_cleaned.json"
    DISCOVERED_STORES_DIR = "C:\\Users\\ethan\\coding\\splitcart\\api\\data\\discovered_stores"

    if not os.path.exists(OUTPUT_FILE):
        print(f"Warning: '{OUTPUT_FILE}' not found. Nothing to process.")
        return

    if not os.path.exists(DISCOVERED_STORES_DIR):
        os.makedirs(DISCOVERED_STORES_DIR)

    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            all_stores = json.load(f)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from '{OUTPUT_FILE}'. File might be corrupted.")
        return

    if not isinstance(all_stores, dict):
        print(f"Error: Expected a dictionary in '{OUTPUT_FILE}', but found {type(all_stores)}. Skipping processing.")
        return

    processed_count = 0
    stores_to_keep = {}

    for store_id, store_data in all_stores.items():
        filename = os.path.join(DISCOVERED_STORES_DIR, f"coles_{store_id}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(store_data, f, indent=4)
            print(f"Processed and saved store {store_id} to {filename}")
            processed_count += 1
        except Exception as e:
            print(f"Error saving store {store_id} to {filename}: {e}")
            stores_to_keep[store_id] = store_data

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stores_to_keep, f, indent=4)

    print(f"Successfully processed {processed_count} stores.")
    if stores_to_keep:
        print(f"{len(stores_to_keep)} stores could not be processed and remain in '{OUTPUT_FILE}'.")
    else:
        print(f"'{OUTPUT_FILE}' has been cleared.")
