import requests
import json
import time
import random
import os
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi
from api.utils.scraper_utils.atomic_scraping_utils import append_to_temp_file, finalize_scrape
from api.utils.scraper_utils.get_aldi_categories import get_aldi_categories

def scrape_and_save_aldi_data(company: str, store_name: str, store_id: str, state: str):
    """
    Launches a requests-based scraper for a specific ALDI store.
    Scrapes all data into a temporary file and moves it to the inbox on success.
    """
    effective_store_name = store_name if store_name else f"ALDI Store {store_id}"
    store_name_slug = f"{slugify(effective_store_name)}-{store_id}"
    print(f"--- Initializing ALDI Scraper for {company} ({store_name_slug}) ---")

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
        })

        categories_to_fetch = get_aldi_categories(store_id, session)
        if not categories_to_fetch:
            print("Could not fetch ALDI categories. Aborting scraper.")
            return

        all_products_data = []
        for category_slug, category_key in categories_to_fetch:
            print(f"\n--- Starting category: '{category_slug}' ---")
            
            limit = 30
            page_num = 1
            offset = 0

            while True:
                print(f"Attempting to fetch page {page_num} for '{category_slug}' (offset: {offset})...")
                
                api_url = "https://api.aldi.com.au/v3/product-search"
                params = {
                    "currency": "AUD", "serviceType": "walk-in", "categoryKey": category_key,
                    "limit": limit, "offset": offset, "sort": "relevance", "testVariant": "A",
                    "servicePoint": store_id,
                }

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    if response.status_code == 400:
                        print(f"Received 400 Bad Request. Assuming end of category '{category_slug}'.")
                        break
                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("data", [])

                    if not raw_products_on_page:
                        print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                        break

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_aldi(
                        raw_product_list=raw_products_on_page, company=company, store_name=effective_store_name, store_id=store_id, state=state,
                        category_slug=category_slug, page_num=page_num, timestamp=scrape_timestamp
                    )
                    
                    products_on_page = data_packet.get('products', [])
                    metadata = data_packet.get('metadata', {})

                    for product in products_on_page:
                        all_products_data.append({"product": product, "metadata": metadata})

                    print(f"Found and cleaned {len(products_on_page)} products on page {page_num}.")

                except requests.exceptions.RequestException as e:
                    print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                    raise
                except json.JSONDecodeError:
                    print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'.")
                    raise

                sleep_time = random.uniform(0.5, 1.5)
                print(f"Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
                offset += limit
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

