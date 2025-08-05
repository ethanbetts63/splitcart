import json
import os

# Define the directory containing the state files
stores_dir = r'C:\Users\ethan\coding\splitcart\woolworths_stores'
file_paths = [
    os.path.join(stores_dir, f) for f in os.listdir(stores_dir) 
    if f.startswith('woolworths_stores_') and f.endswith('.json')
]

all_stores = {}

# --- 1. Read all stores and deduplicate by name ---
for f_path in file_paths:
    try:
        with open(f_path, 'r') as f:
            data = json.load(f)
            for store in data.get('Stores', []):
                store_name = store.get('Name')
                if store_name and store_name not in all_stores:
                    all_stores[store_name] = store
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f'Could not process {os.path.basename(f_path)}: {e}')

print(f'Found a total of {len(all_stores)} unique stores across all files.')

# --- 2. Re-sort all unique stores by their 'State' field ---
stores_by_state = {}
for store in all_stores.values():
    state = store.get('State', 'other').lower()
    if state not in stores_by_state:
        stores_by_state[state] = []
    stores_by_state[state].append(store)

print('Re-sorted unique stores into their correct states.')

# --- 3. Overwrite each state file with the clean, correct data ---
for state, state_stores in stores_by_state.items():
    output_path = os.path.join(stores_dir, f'woolworths_stores_{state}.json')
    with open(output_path, 'w') as f_out:
        # Sort stores by name within each file for consistency
        sorted_stores = sorted(state_stores, key=lambda x: x.get('Name', ''))
        json.dump({'Stores': sorted_stores}, f_out, indent=2)
        print(f'Wrote {len(sorted_stores)} stores to {os.path.basename(output_path)}.')

# --- 4. Optional: Clean up any state files that are now empty ---
existing_state_keys = {s.lower() for s in stores_by_state.keys()}
for f_path in file_paths:
    state_key_from_fname = os.path.basename(f_path).replace('woolworths_stores_', '').replace('.json', '')
    if state_key_from_fname not in existing_state_keys:
        print(f'Removing empty or now-redundant file: {os.path.basename(f_path)}')
        os.remove(f_path)

print('Cleanup complete.')
