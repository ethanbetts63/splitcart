import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga

def scrape_and_save_iga_data(company: str, stores_to_scrape: list, categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper for IGA, iterating through specified stores
    and their specific subcategories.
    """
    print("--- Initializing IGA Scraper Tool ---")
    
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    for store_info in stores_to_scrape:
        store_name = store_info['store_name']
        store_id = store_info['store_id']
        print(f"\n--- Starting Store: {store_name} (ID: {store_id}) ---")
        
        for category_name in categories_to_fetch:
            print(f"  -- Starting category: '{category_name}' --")
            
            skip = 0
            take = 36
            page_num = 1
            previous_page_skus = set()

            while True:
                print(f"    Attempting to fetch page {page_num} for '{category_name}' (skip: {skip})...")
                
                # The category name in the URL needs to be URL-encoded (e.g., spaces become %20)
                api_url = f"https://www.igashop.com.au/api/storefront/stores/{store_id}/categories/{requests.utils.quote(category_name)}/search"
                params = {'take': take, 'skip': skip}

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    
                    if response.status_code == 404:
                        print(f"    Category '{category_name}' not found for this store. Skipping.")
                        break

                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("items", [])

                    if not raw_products_on_page:
                        print(f"    Page {page_num} is empty. End of category '{category_name}'.")
                        break

                    # --- Infinite Loop Prevention ---
                    current_page_skus = {product.get('sku') for product in raw_products_on_page}
                    if current_page_skus == previous_page_skus:
                        print(f"    WARNING: Duplicate products detected on page {page_num}. This indicates a potential infinite loop. Stopping category.")
                        break
                    previous_page_skus = current_page_skus
                    # --- End of Prevention Logic ---

                    scrape_timestamp = datetime.now()
                    category_slug = category_name.lower().replace(' & ', '-').replace(' ', '-').replace(',', '')
                    data_packet = clean_raw_data_iga(
                        raw_product_list=raw_products_on_page, company=company,
                        store=store_name, category_slug=category_slug,
                        page_num=page_num, timestamp=scrape_timestamp
                    )
                    print(f"    Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                    file_name = f"{company}_{store_name}_{category_slug}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
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
