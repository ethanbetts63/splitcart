import os
import json
import requests
import time

def update_iga_store_ids():
    """
    Iterates through state-based IGA store files, fetches the correct
    retailerStoreId from the IGA API using the 'tag' field, and updates
    the JSON files with this new ID.
    """
    base_path = os.path.join('C:', os.sep, 'Users', 'ethan', 'coding', 'splitcart')
    input_dir = os.path.join(base_path, 'api', 'data', 'store_data', 'stores_iga')

    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found at {input_dir}")
        return

    for filename in os.listdir(input_dir):
        if filename.endswith('.json') and 'by_state' not in filename:
            file_path = os.path.join(input_dir, filename)
            print(f"--- Processing {filename} ---")
            
            try:
                # Open with r+ to read and then write
                with open(file_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    stores_to_process = data.get('stores', [])
                    
                    if not stores_to_process:
                        print(f"No stores found in {filename}. Skipping.")
                        continue

                    # Modify the list of stores in-place
                    for store in stores_to_process:
                        tag = store.get('tag')
                        if not tag:
                            print(f"Warning: Store '{store.get('storeName')}' is missing a 'tag'. Skipping.")
                            continue

                        try:
                            api_url = f"https://www.igashop.com.au/api/storefront/stores?RSID={tag}&take=1"
                            response = requests.get(api_url, timeout=10)
                            response.raise_for_status()
                            api_data = response.json()

                            if api_data.get('items'):
                                retailer_store_id = api_data['items'][0].get('retailerStoreId')
                                if retailer_store_id:
                                    # Add the new ID to the store dictionary
                                    store['retailerStoreId'] = retailer_store_id
                                    print(f"Successfully updated '{store.get('storeName')}' with retailer ID: {retailer_store_id}")
                                else:
                                    print(f"Warning: 'retailerStoreId' not found in API response for tag {tag}.")
                            else:
                                print(f"Warning: No 'items' in API response for tag {tag}.")
                                
                        except requests.exceptions.RequestException as e:
                            print(f"Error fetching data for tag {tag}: {e}")
                        
                        time.sleep(0.5) # Be respectful to the API

                    # Go back to the beginning of the file to overwrite it
                    f.seek(0)
                    # Write the updated data back to the file
                    json.dump(data, f, indent=4)
                    # Truncate the file in case the new content is smaller
                    f.truncate()

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not decode JSON from {filename}. Skipping. Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred with {filename}: {e}")

    print("\n--- All state files have been processed. ---")

if __name__ == "__main__":
    update_iga_store_ids()