
import os
import json

def create_iga_store_lists():
    """
    Reads all state-based JSON files for IGA stores, extracts store name and ID,
    and compiles them into a single JSON file with a metadata block,
    categorized by state.
    """
    base_path = os.path.join('C:', os.sep, 'Users', 'ethan', 'coding', 'splitcart')
    input_dir = os.path.join(base_path, 'api', 'data', 'store_data', 'stores_iga')
    output_file = os.path.join(input_dir, 'iga_stores_by_state.json')

    stores_by_state = {}

    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found at {input_dir}")
        return

    # Use sorted list of filenames to ensure consistent state order
    sorted_filenames = sorted(os.listdir(input_dir))

    for filename in sorted_filenames:
        if filename.endswith('.json'):
            # Clean up filename to get state key, handling potential spaces
            state_key = filename.replace('.json', '').strip().upper()
            if not state_key or 'BY_STATE' in state_key:
                continue # Skip invalid or previously generated files

            stores_by_state[state_key] = []
            file_path = os.path.join(input_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not decode JSON from {filename}. Skipping. Error: {e}")
                continue

            for store in data.get('stores', []):
                store_name = store.get('storeName')
                store_id = store.get('storeId')
                
                if store_name and store_id:
                    stores_by_state[state_key].append({
                        'store_name': store_name,
                        'store_id': str(store_id) # Ensure ID is a string
                    })

    # Sort stores within each state alphabetically by name
    for state in stores_by_state:
        stores_by_state[state] = sorted(stores_by_state[state], key=lambda x: x['store_name'])

    # Determine the first state for the initial metadata
    first_state = next(iter(stores_by_state)) if stores_by_state else None

    # Create the final structure with metadata
    output_data = {
        "metadata": {
            "next_state_to_scrape": first_state,
            "last_scraped_timestamp": None,
            "total_stores_scraped": 0
        },
        "stores_by_state": stores_by_state
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print(f"Successfully created {output_file} with metadata structure.")

if __name__ == "__main__":
    create_iga_store_lists()
