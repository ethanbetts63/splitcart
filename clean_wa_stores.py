import json

f_path = r'C:\Users\ethan\coding\splitcart\woolworths_stores_wa.txt'

try:
    with open(f_path, 'r') as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f'Error reading or parsing file: {e}')
    exit()

original_stores = data.get('Stores', [])
keys_to_keep = ['Division', 'Name', 'AddressLine1', 'Suburb', 'State', 'Postcode']
cleaned_stores = []

for store in original_stores:
    # Process only supermarkets, as requested previously
    if store.get('Division') == 'SUPERMARKETS':
        cleaned_store = {key: store.get(key) for key in keys_to_keep}
        cleaned_stores.append(cleaned_store)

final_data = {'Stores': cleaned_stores}

with open(f_path, 'w') as f:
    json.dump(final_data, f, indent=2)

print(f'Successfully cleaned and formatted {f_path}. Total stores processed: {len(cleaned_stores)}.')
