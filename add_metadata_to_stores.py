import json
import os

stores_dir = r'C:\Users\ethan\coding\splitcart\woolworths_stores'
file_paths = [
    os.path.join(stores_dir, f) for f in os.listdir(stores_dir) 
    if f.startswith('woolworths_stores_') and f.endswith('.json')
]

for f_path in file_paths:
    try:
        with open(f_path, 'r') as f:
            data = json.load(f)
        
        stores = data.get('Stores', [])
        num_stores = len(stores)
        # Extract state from filename, e.g., 'woolworths_stores_nsw.json' -> 'NSW'
        state = os.path.basename(f_path).replace('woolworths_stores_', '').replace('.json', '').upper()

        metadata = {
            'state': state,
            'store_count': num_stores
        }

        # Create the new data structure
        new_data = {
            'metadata': metadata,
            'Stores': stores
        }

        with open(f_path, 'w') as f_out:
            json.dump(new_data, f_out, indent=2)
        
        print(f'Successfully added metadata to {os.path.basename(f_path)}')

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f'Could not process {os.path.basename(f_path)}: {e}')

print('Metadata addition complete.')
