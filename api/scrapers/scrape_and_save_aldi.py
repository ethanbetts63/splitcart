import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi

def scrape_and_save_aldi_data(categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper, iterates through all pages of the given
    ALDI categories by hitting its API, cleans the data, and saves it to a file.
    """
    print("--- Initializing ALDI Scraper Tool ---")
    
    session = requests.Session()
    # ALDI's API does not require extensive headers, but a user-agent is good practice.
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    for category_slug, category_key in categories_to_fetch:
        print(f"\n--- Starting category: '{category_slug}' ---")
        
        offset = 0
        limit = 30  # The API seems to default to 30, so we'll stick with that.
        page_num = 1

        while True:
            print(f"Attempting to fetch page {page_num} for '{category_slug}' (offset: {offset})...")
            
            api_url = "https://api.aldi.com.au/v3/product-search"
            # These parameters are based on the API call discovered earlier.
            params = {
                "currency": "AUD",
                "serviceType": "walk-in",
                "categoryKey": category_key,
                "limit": limit,
                "offset": offset,
                "sort": "relevance",
                "testVariant": "A",
                "servicePoint": "G452", # This may need updating if it's session-specific
            }

            try:
                response = session.get(api_url, params=params, timeout=60)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                data = response.json()
                
                raw_products_on_page = data.get("data", [])

                if not raw_products_on_page:
                    print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                    break

                # Pass the raw data to the new cleaner function
                scrape_timestamp = datetime.now()
                data_packet = clean_raw_data_aldi(raw_products_on_page, category_slug, page_num, scrape_timestamp)
                print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                # Save the cleaned data packet to a JSON file
                file_name = f"aldi_{category_slug.replace('/', '_')}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_packet, f, indent=4)
                print(f"Successfully saved cleaned data to {file_name}")

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                break
            except json.JSONDecodeError:
                print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'. The response may not be valid JSON.")
                break

            # Be a good internet citizen
            sleep_time = random.uniform(1, 3)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            # Prepare for the next page
            offset += limit
            page_num += 1
        
        print(f"--- Finished category: '{category_slug}' ---")
            
    print("\n--- ALDI scraper tool finished. ---")
