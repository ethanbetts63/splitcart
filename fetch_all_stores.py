import requests
import json
import html
import re

def parse_stores_from_html(html_content):
    stores = []
    store_data_matches = re.findall(r'data-storedata="([^"]+)"', html_content)

    for store_data_str in store_data_matches:
        decoded_str = html.unescape(store_data_str)
        try:
            store_data = json.loads(decoded_str)
            stores.append(store_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Problematic string: {decoded_str}")

    return stores

def fetch_all_stores():
    stores_file = 'C:\\Users\\ethan\\coding\\splitcart\\stores.json'

    # Load existing stores
    try:
        with open(stores_file, 'r', encoding='utf-8') as f:
            all_stores_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_stores_data = []

    existing_store_ids = {store['storeId'] for store in all_stores_data}
    stores_to_check = list(existing_store_ids)
    checked_store_ids = set()

    # Broad search: Iterate through potential store IDs
    print("Performing broad search for stores...")
    for initial_store_id in range(1, 25001, 50): # From 1 to 25000, step 50
        if str(initial_store_id) in checked_store_ids:
            continue

        print(f"Checking initial store ID: {initial_store_id}")
        url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={initial_store_id}&callback=jQuery17209679725593495141_1754480497404&_=1754480498902"
        
        try:
            response = requests.get(url)
            response.raise_for_status() # Raise an exception for bad status codes
            
            # Extract JSON from JSONP
            jsonp_content = response.text
            start_index = jsonp_content.find('(')
            end_index = jsonp_content.rfind(')')

            if start_index != -1 and end_index != -1:
                json_str = jsonp_content[start_index + 1:end_index]
                data = json.loads(json_str)
                html_content = data.get('content', '')
            else:
                # If JSONP parsing fails, it might be a direct JSON response or an error
                # Try to parse as direct JSON first
                try:
                    data = json.loads(jsonp_content)
                    html_content = data.get('content', '')
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSONP or JSON response")

            new_stores = parse_stores_from_html(html_content)

            for store in new_stores:
                if store['storeId'] not in existing_store_ids:
                    all_stores_data.append(store)
                    existing_store_ids.add(store['storeId'])
                    stores_to_check.append(store['storeId'])
                    print(f"  Found new store: {store['storeName']} ({store['storeId']})")

            checked_store_ids.add(str(initial_store_id)) # Add initial_store_id to checked

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for initial store ID {initial_store_id}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response for initial store ID {initial_store_id}: {e}")
            # print(f"Raw response content:\n{response.text}") # Uncomment for detailed debugging
        except ValueError as e:
            print(f"Error processing response for initial store ID {initial_store_id}: {e}")
            # print(f"Raw response content:\n{response.text}") # Uncomment for detailed debugging

    print("Broad search complete. Continuing with iterative search...")

    # Existing iterative search
    while stores_to_check:
        store_id = stores_to_check.pop(0)
        if store_id in checked_store_ids:
            continue

        print(f"Fetching stores near: {store_id}")
        url = f"https://embed.salefinder.com.au/location/storelocator/183/?format=json&saleGroup=0&limit=1500&locationId={store_id}&callback=jQuery17209679725593495141_1754480497404&_=1754480498902"
        
        try:
            response = requests.get(url)
            response.raise_for_status() # Raise an exception for bad status codes
            
            # Extract JSON from JSONP
            jsonp_content = response.text
            start_index = jsonp_content.find('(')
            end_index = jsonp_content.rfind(')')

            if start_index != -1 and end_index != -1:
                json_str = jsonp_content[start_index + 1:end_index]
                data = json.loads(json_str)
                html_content = data.get('content', '')
            else:
                # If JSONP parsing fails, it might be a direct JSON response or an error
                # Try to parse as direct JSON first
                try:
                    data = json.loads(jsonp_content)
                    html_content = data.get('content', '')
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSONP or JSON response")
            new_stores = parse_stores_from_html(html_content)

            for store in new_stores:
                if store['storeId'] not in existing_store_ids:
                    all_stores_data.append(store)
                    existing_store_ids.add(store['storeId'])
                    stores_to_check.append(store['storeId'])
                    print(f"  Found new store: {store['storeName']} ({store['storeId']})")

            checked_store_ids.add(store_id)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for store ID {store_id}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response for store ID {store_id}: {e}")
            # print(f"Raw response content:\n{response.text}") # Uncomment for detailed debugging
        except ValueError as e:
            print(f"Error processing response for store ID {store_id}: {e}")
            # print(f"Raw response content:\n{response.text}") # Uncomment for detailed debugging

    # Write all stores back to the file
    with open(stores_file, 'w', encoding='utf-8') as f:
        json.dump(all_stores_data, f, indent=4)

    print(f"Finished. Found {len(all_stores_data)} total stores.")

if __name__ == "__main__":
    fetch_all_stores()
