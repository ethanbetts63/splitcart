import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths

def scrape_and_save_woolworths_data(company: str, store: str, categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper, iterates through all pages of the given
    Woolworths categories, cleans the data, and saves it to a file.
    """
    print(f"--- Initializing Woolworths Scraper Tool for {company} ({store}) ---")
    
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    for category_slug, category_id in categories_to_fetch:
        print(f"\n--- Starting category: '{category_slug}' ---")
        
        page_num = 1
        while True:
            print(f"Attempting to fetch page {page_num} for '{category_slug}'...")
            
            api_url = "https://www.woolworths.com.au/apis/ui/browse/category"
            payload = {
                "categoryId": category_id, "pageNumber": page_num, "pageSize": 36,
                "sortType": "PriceAsc", "url": f"/shop/browse/{category_slug}",
            }

            try:
                response = session.post(api_url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = []
                for bundle in data.get("Bundles", []):
                    if bundle and bundle.get("Products"):
                        raw_products_on_page.extend(bundle.get("Products"))

                if not raw_products_on_page:
                    print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                    break

                scrape_timestamp = datetime.now()
                data_packet = clean_raw_data_woolworths(
                    raw_product_list=raw_products_on_page,
                    company=company,
                    store=store,
                    category=category_slug,
                    page_num=page_num,
                    timestamp=scrape_timestamp
                )
                print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                file_name = f"{company.lower()}_{store.lower()}_{category_slug}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_packet, f, indent=4)
                print(f"Successfully saved cleaned data to {file_name}")

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                break
            except json.JSONDecodeError:
                print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'.")
                break

            sleep_time = random.uniform(2, 5)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            page_num += 1
        
        print(f"--- Finished category: '{category_slug}' ---")
            
    print("\n--- Woolworths scraper tool finished. ---")
