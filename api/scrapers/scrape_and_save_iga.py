import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

def scrape_and_save_iga_data(company: str, stores_to_scrape: list, save_path: str):
    """
    Launches a requests-based scraper for IGA, iterating through specified stores
    and their categories, cleaning the data, and saving it to JSON files.
    """
    print("--- Initializing IGA Scraper Tool ---")
    
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    # A placeholder list of categories to attempt to scrape for each store.
    # This should be replaced with a dynamic category fetch if an endpoint is found.
    categories_to_try = [
        'Fruit', 'Vegetables', 'Meat', 'Poultry', 'Dairy', 'Bakery', 'Pantry',
        'Drinks', 'Freezer', 'Health & Beauty', 'Household'
    ]

    for store_info in stores_to_scrape:
        store_name = store_info['store_name']
        store_id = store_info['store_id']
        print(f"\n--- Starting Store: {store_name} (ID: {store_id}) ---")

        # The sessionId might be required. We can try to get one with a warm-up call.
        # For now, we will attempt without one, as the API might not strictly require it.
        
        for category_name in categories_to_try:
            print(f"  -- Starting category: '{category_name}' --")
            
            skip = 0
            take = 36 # A reasonable page size
            page_num = 1

            while True:
                print(f"    Attempting to fetch page {page_num} for '{category_name}' (skip: {skip})...")
                
                api_url = f"https://www.igashop.com.au/api/storefront/stores/{store_id}/categories/{category_name}/search"
                params = {
                    'take': take,
                    'skip': skip,
                }

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    
                    # IGA's API might return 404 for a category that doesn't exist.
                    if response.status_code == 404:
                        print(f"    Category '{category_name}' not found for this store. Skipping.")
                        break

                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("items", [])

                    if not raw_products_on_page:
                        print(f"    Page {page_num} is empty. Assuming end of category '{category_name}'.")
                        break

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_iga(
                        raw_product_list=raw_products_on_page,
                        company=company,
                        store=store_name,
                        category_slug=category_name.lower().replace(' & ', '-').replace(' ', '-'),
                        page_num=page_num,
                        timestamp=scrape_timestamp
                    )
                    print(f"    Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                    file_name = f"{company}_{store_name}_{data_packet['metadata']['category']}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data_packet, f, indent=4)
                    print(f"    Successfully saved cleaned data to {file_name}")

                except requests.exceptions.RequestException as e:
                    print(f"    ERROR: Request failed on page {page_num} for '{category_name}': {e}")
                    break
                except json.JSONDecodeError:
                    print(f"    ERROR: Failed to decode JSON on page {page_num} for '{category_name}'.")
                    break

                sleep_time = random.uniform(2, 4)
                print(f"    Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
                skip += take
                page_num += 1
            
            print(f"  -- Finished category: '{category_name}' --")
            
    print("\n--- IGA scraper tool finished. ---")
