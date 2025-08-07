
import os
import json

def remove_retailerstoreid_field():
    """
    Iterates through state-based IGA store files and removes the
    'retailerStoreId' field from each store object.
    """
    base_path = os.path.join('C:', os.sep, 'Users', 'ethan', 'coding', 'splitcart')
    stores_dir = os.path.join(base_path, 'api', 'data', 'store_data', 'stores_iga')

    if not os.path.exists(stores_dir):
        print(f"Error: Stores directory not found at {stores_dir}")
        return

    print("--- Removing 'retailerStoreId' field from state JSON files ---")
    for filename in os.listdir(stores_dir):
        if filename.endswith('.json') and 'by_state' not in filename:
            file_path = os.path.join(stores_dir, filename)
            file_was_modified = False
            
            try:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    stores = data.get('stores', [])

                    for store in stores:
                        if 'retailerStoreId' in store:
                            del store['retailerStoreId']
                            file_was_modified = True
                    
                    if file_was_modified:
                        print(f"Removed 'retailerStoreId' from stores in {filename}.")
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not process {filename}. Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred with {filename}: {e}")

    print("\n--- Finished cleaning all state files. ---")

if __name__ == "__main__":
    remove_retailerstoreid_field()
