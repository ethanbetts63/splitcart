import requests
import json
import time
import random
import os
from datetime import datetime
from django.conf import settings
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi
from api.utils.scraper_utils.get_aldi_categories import get_aldi_categories
from api.utils.scraper_utils.jsonl_writer import JsonlWriter

def scrape_and_save_aldi_data(company: str, store_name: str, store_id: str, state: str):
    """
    Launches a requests-based scraper for a specific ALDI store.
    Scrapes all data into a temporary file and moves it to the inbox on success.
    """
    effective_store_name = store_name if store_name else f"ALDI Store {store_id}"
    store_name_slug = f"{slugify(effective_store_name)}-{store_id}"
    print(f"--- Initializing ALDI Scraper for {company} ({store_name_slug}) ---")

    scrape_successful = False
    jsonl_writer = JsonlWriter(company, store_name_slug, state)

    try:
        session = requests.Session()
        session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })

        categories_to_fetch = get_aldi_categories(store_id, session)
        if not categories_to_fetch:
            print("Could not fetch ALDI categories. Aborting scraper.")
            return

        jsonl_writer.open() # Open the JSONL file

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
                        raw_product_list=raw_products_on_page, company=company, store_name=effective_store_name, store_id=store_id, state=state, timestamp=scrape_timestamp
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

                sleep_time = random.uniform(0.5, 1.5)
                print(f"Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
                offset += limit
                page_num += 1

        scrape_successful = True
        print(f"\n--- All categories for '{store_name_slug}' scraped successfully. ---")

    finally:
        jsonl_writer.finalize(scrape_successful)

