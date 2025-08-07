import os
import json
import re

def parse_and_update_from_log_corrected():
    """
    Parses the retailer_ids_iga.txt log file to find successfully updated
    retailer IDs and updates the 'retailerStoreId' field in the corresponding state JSON files.
    Ensures every store has a 'retailerStoreId' key.
    """
    base_path = os.path.join('C:', os.sep, 'Users', 'ethan', 'coding', 'splitcart')
    log_file_path = os.path.join(base_path, 'retailer_ids_iga.txt')
    stores_dir = os.path.join(base_path, 'api', 'data', 'store_data', 'stores_iga')

    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at {log_file_path}")
        return

    # 1. Parse the log file to create a map of store names to retailer IDs
    store_id_map = {}
    regex = r"Successfully updated '(.+?)' with retailer ID: (\d+)"

    print("--- Parsing log file to find successful updates ---")
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(regex, line)
            if match:
                store_name = match.group(1).strip()
                retailer_id = match.group(2).strip()
                store_id_map[store_name] = retailer_id
    
    print(f"Found {len(store_id_map)} successfully updated stores in the log.")

    # 2. Iterate through state JSON files and update them
    if not os.path.exists(stores_dir):
        print(f"Error: Stores directory not found at {stores_dir}")
        return

    print("\n--- Updating state JSON files with 'retailerStoreId' ---")
    for filename in os.listdir(stores_dir):
        if filename.endswith('.json') and 'by_state' not in filename:
            file_path = os.path.join(stores_dir, filename)
            updated_in_file = False
            
            try:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    stores = data.get('stores', [])

                    for store in stores:
                        # Ensure the retailerStoreId key exists
                        if 'retailerStoreId' not in store:
                            store['retailerStoreId'] = ""

                        store_name = store.get('storeName')
                        if store_name in store_id_map:
                            new_id = store_id_map[store_name]
                            if store['retailerStoreId'] != new_id:
                                store['retailerStoreId'] = new_id
                                print(f"Updated '{store_name}' in {filename} with retailerStoreId: {new_id}")
                                updated_in_file = True
                    
                    # If any updates were made, write back to the file
                    if updated_in_file:
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not process {filename}. Error: {e}")

    print("\n--- Finished updating all state files. ---")

if __name__ == "__main__":
    parse_and_update_from_log_corrected()