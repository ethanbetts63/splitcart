
import requests
import json
import re
import time

def fetch_all_stores():
    """
    Iterates through Australian postcodes, fetches store data from Sale Finder,
    and saves all responses into a single JSON file.
    """
    all_stores = []
    # Postcodes range from 0000 to 8000, iterating by 50
    for postcode in range(0, 8001, 50):
        # Format the postcode to be 4 digits with leading zeros
        query = f"{postcode:04d}"
        target_url = f"https://embed.salefinder.com.au/location/search/183/?query={query}&sensitivity=5&noStoreSuffix=1&withStoreInfo=1"
        
        print(f"Fetching data for postcode range around: {query}")

        try:
            response = requests.get(target_url, timeout=20)
            response.raise_for_status()

            jsonp_content = response.text
            match = re.search(r'\((.*)\)', jsonp_content)
            if not match:
                print(f"  - Could not extract JSON for postcode {query}.")
                continue

            json_data_string = match.group(1)
            data = json.loads(json_data_string)

            if data.get("suggestions"):
                all_stores.extend(data["suggestions"])
                print(f"  - Found {len(data['suggestions'])} stores.")
        
        except requests.exceptions.RequestException as e:
            print(f"  - Error fetching data for postcode {query}: {e}")
        except json.JSONDecodeError:
            print(f"  - Failed to decode JSON for postcode {query}.")
        
        # A short delay to avoid overwhelming the server
        time.sleep(0.5)

    # Save all collected stores to a single file
    output_file = "all_stores_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_stores, f, indent=4)

    print(f"\n--- All postcodes processed. ---")
    print(f"Saved {len(all_stores)} stores to {output_file}")

if __name__ == "__main__":
    fetch_all_stores()
