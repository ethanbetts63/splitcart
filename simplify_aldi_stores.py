
import json
import sys
import os

input_file = 'C:\\Users\\ethan\\coding\\splitcart\\aldi_all_stores.txt'
output_file = 'C:\\Users\\ethan\\coding\\splitcart\\aldi_all_stores.txt.tmp'

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Check if the file is already simplified
        if content.strip().startswith('['):
            print("File is already simplified.")
            sys.exit(0)
        data = json.loads(content)

    simplified_stores = []
    for store in data.get('response', {}).get('entities', []):
        profile = store.get('profile', {})
        address = profile.get('address', {})
        
        simplified_store = {
            'city': address.get('city'),
            'line1': address.get('line1'),
            'postcode': address.get('postalCode'),
            'region': address.get('region'),
            'c_internalALDIID': profile.get('c_internalALDIID'),
            'c_locationName': profile.get('c_locationName')
        }
        simplified_stores.append(simplified_store)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified_stores, f, indent=4)

    os.replace(output_file, input_file)
    print("File simplified successfully.")

except json.JSONDecodeError:
    print("Error decoding JSON. The file might be corrupted or not in the expected format.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
    if os.path.exists(output_file):
        os.remove(output_file)
    sys.exit(1)
