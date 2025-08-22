import requests
import json
import time
import random
import os
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga
from api.utils.scraper_utils.get_iga_categories import get_iga_categories
from api.utils.scraper_utils.atomic_scraping_utils import append_to_temp_file, finalize_scrape
import uuid

def scrape_and_save_iga_data(company: str, store_id: str, retailer_store_id: str, store_name: str, store_name_slug: str, state: str):
    """
    Launches a requests-based scraper for IGA.
    Scrapes all data into a temporary file and moves it to the inbox on success.
    """
    print("--- Initializing IGA Scraper Tool ---")

    if not retailer_store_id:
        print(f"    Skipping {store_name} as it has no retailerStoreId, indicating it's not an online store.")
        return False

    temp_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'temp_inbox')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_file_path = os.path.join(temp_dir, f"temp_{store_name_slug}.jsonl")
    inbox_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'product_inbox')

    scrape_successful = False

    try:
        session = requests.Session()
        session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
            "x-shopping-mode": "11111111-1111-1111-1111-111111111111"
        })
        session.cookies.set("iga-shop.retailerStoreId", retailer_store_id)

        print(f"\n--- Starting Store: {store_name} (Retailer ID: {retailer_store_id}) ---")

        try:
            print("    Initializing session by visiting homepage...")
            session.get("https://www.igashop.com.au/", timeout=60)
            print("    Session initialized.")
        except requests.exceptions.RequestException as e:
            print(f"    ERROR: Could not initialize session. Error: {e}")
            return False

        session_id = str(uuid.uuid4())
        print(f"    Generated session ID for product search: {session_id}")

        categories_to_fetch = get_iga_categories(retailer_store_id, session)
        if not categories_to_fetch:
            print(f"Could not retrieve categories for {store_name}. Skipping.")
            return False

        all_products_data = []
        for category_data in categories_to_fetch:
            category_name = category_data['displayName']
            category_identifier = category_data['identifier']
            category_slug = slugify(category_name)

            print(f"  -- Starting category: '{category_name}' --")
            
            take = 36
            page_num = 1
            skip = 0

            previous_page_skus = set()
            while True:
                print(f"    Attempting to fetch page {page_num} for '{category_name}' (skip: {skip})...")
                
                api_url = f"https://www.igashop.com.au/api/storefront/stores/{retailer_store_id}/categories/{requests.utils.quote(category_identifier)}/search"
                params = {'take': take, 'skip': skip, 'sessionId': session_id}

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    if response.status_code == 404:
                        print(f"    Category '{category_name}' not found. Skipping.")
                        break
                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("items", [])

                    if not raw_products_on_page:
                        print(f"    Page {page_num} is empty. End of category.")
                        break

                    current_page_skus = {p.get('sku') for p in raw_products_on_page}
                    if current_page_skus == previous_page_skus:
                        print(f"    WARNING: Duplicate products detected. Stopping category.")
                        break
                    previous_page_skus = current_page_skus

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_iga(
                        raw_product_list=raw_products_on_page, company=company,
                        store_id=store_id, store_name=store_name, state=state,
                        category_slug=category_slug, page_num=page_num, timestamp=scrape_timestamp
                    )
                    
                    products_on_page = data_packet.get('products', [])
                    metadata = data_packet.get('metadata', {})
                    
                    for product in products_on_page:
                        all_products_data.append({"product": product, "metadata": metadata})

                    print(f"    Found and cleaned {len(products_on_page)} products on page {page_num}.")

                except requests.exceptions.RequestException as e:
                    print(f"    ERROR: Request failed: {e}")
                    raise
                except json.JSONDecodeError:
                    print(f"    ERROR: Failed to decode JSON.")
                    raise

                sleep_time = random.uniform(0.5, 1.5)
                print(f"    Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
                skip += take
                page_num += 1

        with open(temp_file_path, 'w', encoding='utf-8') as f:
            for product_data in all_products_data:
                json.dump(product_data, f)
                f.write('\n')

        scrape_successful = True
        print(f"\n--- All categories for '{store_name_slug}' scraped successfully. ---")

    finally:
        if scrape_successful:
            print(f"Finalizing scrape for {store_name_slug}.")
            final_file_name = f"{company.lower()}_{state.lower()}_{store_name_slug}.jsonl"
            finalize_scrape(temp_file_path, os.path.join(inbox_path, final_file_name))
            print(f"Successfully moved temp file to inbox for {store_name_slug}.")
        else:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            print(f"Scrape for {store_name_slug} failed. Temporary file removed.")

    return scrape_successful
