import requests
import json
import time
import random
from datetime import datetime
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi
from api.utils.scraper_utils.get_aldi_categories import get_aldi_categories
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.utils.scraper_utils.output_utils import ScraperOutput

def scrape_and_save_aldi_data(command, company: str, store_name: str, store_id: str, state: str):
    """
    Launches a requests-based scraper for a specific ALDI store.
    Scrapes all data into a file and moves it to the inbox on success.
    """
    effective_store_name = store_name if store_name else f"ALDI Store {store_id}"
    store_name_slug = f"{slugify(effective_store_name)}-{store_id}"
    
    output = ScraperOutput(command, company, effective_store_name)
    
    scrape_successful = False
    jsonl_writer = JsonlWriter(company, store_name_slug, state)

    try:
        session = requests.Session()
        session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
        })

        categories_to_fetch = get_aldi_categories(command, store_id, session)
        if not categories_to_fetch:
            return

        total_categories = len(categories_to_fetch)
        output.update_progress(total_categories=total_categories)

        jsonl_writer.open()

        for i, (category_slug, category_key) in enumerate(categories_to_fetch):
            output.update_progress(categories_scraped=i + 1)
            
            limit = 30
            page_num = 1
            offset = 0

            while True:
                api_url = "https://api.aldi.com.au/v3/product-search"
                params = {
                    "currency": "AUD", "serviceType": "walk-in", "categoryKey": category_key,
                    "limit": limit, "offset": offset, "sort": "relevance", "testVariant": "A",
                    "servicePoint": store_id,
                }

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    if response.status_code == 400:
                        break
                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("data", [])

                    if not raw_products_on_page:
                        break

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_aldi(
                        raw_product_list=raw_products_on_page, company=company, store_name=effective_store_name, store_id=store_id, state=state, timestamp=scrape_timestamp
                    )
                    
                    products_on_page = data_packet.get('products', [])
                    
                    new_products_count = 0
                    duplicate_products_count = 0
                    for product in products_on_page:
                        if jsonl_writer.write_product(product, {}):
                            new_products_count += 1
                        else:
                            duplicate_products_count +=1

                    output.update_progress(new_products=new_products_count, duplicate_products=duplicate_products_count, pages_scraped=1)

                except (requests.exceptions.RequestException, json.JSONDecodeError):
                    raise

                time.sleep(random.uniform(0.5, 1.5))
                
                offset += limit
                page_num += 1

        scrape_successful = True

    finally:
        jsonl_writer.finalize(scrape_successful)
        output.finalize()