import json
import html
import re


def parse_and_clean_stores(html_content):
    """Parses store data from HTML and returns a cleaned list of store dictionaries."""
    stores = []
    store_data_matches = re.findall(r'data-storedata="([^"]+)"', html_content)
    for store_data_str in store_data_matches:
        decoded_str = html.unescape(store_data_str)
        try:
            store_data = json.loads(decoded_str)
            # Clean the dictionary by removing the 'distance' key
            if 'distance' in store_data:
                del store_data['distance']
            stores.append(store_data)
        except json.JSONDecodeError as e:
            print(f"\nError decoding JSON: {e}")
            print(f"Problematic string: {decoded_str}")
    return stores