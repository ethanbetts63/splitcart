import os
import json

def create_aldi_stores_by_state_file():
    """
    Aggregates individual ALDI store data files into a single aldi_stores_by_state.json file.
    """
    source_directory = os.path.join('api', 'data', 'store_data', 'stores_aldi')
    output_filepath = os.path.join(source_directory, 'aldi_stores_by_state.json')

    aldi_stores_by_state = {
        "metadata": {
            "last_updated": "",
            "total_stores": 0
        },
        "stores_by_state": {}
    }

    total_stores_count = 0

    if not os.path.exists(source_directory):
        print(f"Error: Source directory not found: {source_directory}")
        return

    for filename in os.listdir(source_directory):
        if filename.endswith('.json') and filename != 'aldi_stores_by_state.json':
            file_path = os.path.join(source_directory, filename)
            print(f"Processing: {filename}")

            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    # Assuming each file contains a list of store objects directly
                    # or a dictionary with a 'stores' key containing a list.
                    stores_in_file = []
                    if isinstance(data, list):
                        stores_in_file = data
                    elif isinstance(data, dict) and 'stores' in data:
                        stores_in_file = data['stores']
                    
                    for store in stores_in_file:
                        store_name = store.get('storeName')
                        retailer_id = store.get('retailerId')
                        state = store.get('state')

                        if store_name and retailer_id and state:
                            if state not in aldi_stores_by_state['stores_by_state']:
                                aldi_stores_by_state['stores_by_state'][state] = []
                            
                            aldi_stores_by_state['stores_by_state'][state].append({
                                'store_name': store_name,
                                'retailerId': retailer_id
                            })
                            total_stores_count += 1
                        else:
                            print(f"  Warning: Skipping store in {filename} due to missing storeName, retailerId, or state.")

                except json.JSONDecodeError:
                    print(f"  Warning: Skipping {filename} due to invalid JSON.")

    aldi_stores_by_state['metadata']['last_updated'] = datetime.now().isoformat()
    aldi_stores_by_state['metadata']['total_stores'] = total_stores_count

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(aldi_stores_by_state, f, indent=4)

    print(f"--- Successfully created {os.path.basename(output_filepath)} with {total_stores_count} stores. ---")

if __name__ == '__main__':
    from datetime import datetime
    create_aldi_stores_by_state_file()
