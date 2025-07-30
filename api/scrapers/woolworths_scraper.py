import requests
import json
import time
import random
import os
from datetime import datetime

def scrape_and_save_woolworths_data(categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper, iterates through all pages of the given
    Woolworths categories, and saves each page's product data to a file.

    Args:
        categories_to_fetch: A list of tuples, where each tuple contains
                             (category_slug, category_id).
        save_path: The absolute path to the directory to save JSON files.
    """
    print("--- Initializing Woolworths Scraper Tool ---")
    
    session = requests.Session()
    session.headers.update({
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.woolworths.com.au",
        "referer": "https://www.woolworths.com.au/shop/browse/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    })

    try:
        print("Warming up session to acquire cookies...")
        session.get("https://www.woolworths.com.au/", timeout=60)
        print("Session is ready.")
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL: Failed to warm up session. Error: {e}")
        return

    # Loop through each category
    for category_slug, category_id in categories_to_fetch:
        print(f"\n--- Starting category: '{category_slug}' ---")
        
        page_num = 1
        while True:
            print(f"Attempting to fetch page {page_num} for '{category_slug}'...")
            
            api_url = "https://www.woolworths.com.au/apis/ui/browse/category"
            
            # --- THE FIX: Restored the full, detailed payload ---
            # This payload matches the structure of a real browser request more closely.
            payload = {
                "categoryId": category_id,
                "pageNumber": page_num,
                "pageSize": 36,
                "sortType": "PriceAsc",
                "url": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc",
                "location": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc&filter=SoldBy(Woolworths)",
                "formatObject": f'{{"name":"{category_slug}"}}',
                "isSpecial": False,
                "isBundle": False,
                "isMobile": False,
                "filters": [{"Key": "SoldBy", "Items": [{"Term": "Woolworths"}]}],
                "token": "",
                "gpBoost": 0,
                "isHideUnavailableProducts": False,
                "isRegisteredRewardCardPromotion": False,
                "categoryVersion": "v2",
                "enableAdReRanking": False,
                "groupEdmVariants": False,
                "activePersonalizedViewType": "",
            }

            try:
                response = session.post(api_url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                products_on_page = []
                for bundle in data.get("Bundles", []):
                    if bundle and bundle.get("Products"):
                        products_on_page.extend(bundle.get("Products"))

                if not products_on_page:
                    print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                    break

                print(f"Found {len(products_on_page)} products on page {page_num}.")

                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_name = f"woolworths_{category_slug}_page-{page_num}_{timestamp}.json"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(products_on_page, f, indent=4)
                print(f"Successfully saved data to {file_name}")

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
