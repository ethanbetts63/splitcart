import os
import json
from datetime import datetime

def create_woolworths_stores_by_state():
    # Use absolute paths to avoid issues with working directory
    base_dir = 'C:\\Users\\ethan\\coding\\splitcart'
    woolworths_stores_dir = os.path.join(base_dir, 'api', 'data', 'store_data', 'stores_woolworths', 'supermarkets')
    output_file = os.path.join(base_dir, 'api', 'data', 'store_data', 'stores_woolworths', 'woolworths_stores_by_state.json')

    stores_by_state = {}
    total_stores = 0

    print(f"Reading store files from: {woolworths_stores_dir}")

    state_files = ['act.json', 'nsw.json', 'nt.json', 'qld.json', 'sa.json', 'tas.json', 'vic.json', 'wa.json']
    all_states = [sf.split('.')[0].upper() for sf in state_files]

    for filename in state_files:
        state = filename.split('.')[0].upper()
        file_path = os.path.join(woolworths_stores_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}. Skipping.")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stores = []
                for store in data.get('stores', []):
                    stores.append({
                        'store_name': store.get('Name'),
                        'store_id': store.get('StoreNo')
                    })
                stores_by_state[state] = stores
                total_stores += len(stores)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read or parse {filename}. Error: {e}")
            continue

    print(f"Found a total of {total_stores} stores across {len(all_states)} states.")

    output_data = {
        'metadata': {
            'source': 'https://www.woolworths.com.au/apis/ui/StoreLocator/Stores',
            'total_stores': total_stores,
            'last_scraped_timestamp': None,
            'next_state_to_scrape': all_states[0] if all_states else None
        },
        'stores_by_state': stores_by_state
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print(f"Successfully created consolidated file at: {output_file}")
    except IOError as e:
        print(f"Error: Could not write to output file {output_file}. Error: {e}")

if __name__ == '__main__':
    create_woolworths_stores_by_state()
