import requests
import json
import time
import random
import os
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths
from api.utils.scraper_utils.jsonl_writer import JsonlWriter

def scrape_and_save_woolworths_data(company: str, state: str, stores: list, categories_to_fetch: list):
    """
    Launches a requests-based scraper for a specific Woolworths store.
    Scrapes all data into a  file and moves it to the inbox on success.
    """
    print(f"--- Initializing Woolworths Scraper for {company} in {state} ---")

    for store in stores:
        store_name = store.get("store_name")
        store_id = store.get("store_id")
        store_name_slug = f"{slugify(store_name)}-{store_id}"
        
        print(f"--- Initializing Woolworths Scraper for {company} ({store_name}) ---")

        scrape_successful = False
        jsonl_writer = JsonlWriter(company, store_name_slug, state)

        try:
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

            jsonl_writer.open() # Open the JSONL file

            for category_slug, category_id in categories_to_fetch:
                print(f"\n--- Starting category: '{category_slug}' ---")
                
                page_num = 1
                while True:
                    print(f"Attempting to fetch page {page_num} for '{category_slug}'...")
                    
                    api_url = "https://www.woolworths.com.au/apis/ui/browse/category"
                    payload = {
                        "categoryId": category_id, "pageNumber": page_num, "pageSize": 36,
                        "sortType": "PriceAsc",
                        "url": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc",
                        "location": f"/shop/browse/{category_slug}?pageNumber={page_num}&sortBy=PriceAsc&filter=SoldBy(Woolworths)",
                        "formatObject": f'{{"name":"{category_slug}"}}', "isSpecial": False, "isBundle": False,
                        "isMobile": False, "filters": [{"Key": "SoldBy", "Items": [{"Term": "Woolworths"}]}],
                        "token": "", "gpBoost": 0, "isHideUnavailableProducts": False,
                        "isRegisteredRewardCardPromotion": False, "categoryVersion": "v2",
                        "enableAdReRanking": False, "groupEdmVariants": False, "activePersonalizedViewType": "",
                        "storeId": store_id
                    }

                    try:
                        response = session.post(api_url, json=payload, timeout=60)
                        response.raise_for_status()
                        data = response.json()
                        
                        raw_products_on_page = [p for bundle in data.get("Bundles", []) if bundle and bundle.get("Products") for p in bundle["Products"]]

                        if not raw_products_on_page:
                            print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                            break

                        scrape_timestamp = datetime.now()
                        data_packet = clean_raw_data_woolworths(
                            raw_product_list=raw_products_on_page,
                            company=company, store_id=store_id, store_name=store_name, state=state, timestamp=scrape_timestamp
                        )
                        
                        products_on_page = data_packet.get('products', [])
                        metadata = data_packet.get('metadata', {})

                        products_written_count = 0
                        for product in products_on_page:
                            if jsonl_writer.write_product(product, metadata):
                                products_written_count += 1

                        print(f"Found {len(products_on_page)} products on page {page_num}. Wrote {products_written_count} new products to temp file.")

                    except requests.exceptions.RequestException as e:
                        print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                        raise
                    except json.JSONDecodeError:
                        print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'.")
                        raise

                    sleep_time = random.uniform(0.5, 1)
                    print(f"Waiting for {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    
                    page_num += 1

            scrape_successful = True
            print(f"\n--- All categories for '{store_name}' scraped successfully. ---")

        finally:
            jsonl_writer.finalize(scrape_successful)

