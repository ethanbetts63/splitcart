import requests
import json
import time
import random
import os
from datetime import datetime
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga
from api.utils.scraper_utils.get_iga_categories import get_iga_categories
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.utils.scraper_utils.output_utils import ScraperOutput
import uuid

def scrape_and_save_iga_data(command, company: str, store_id: str, retailer_store_id: str, store_name: str, store_name_slug: str, state: str):
    """
    Launches a requests-based scraper for IGA.
    Scrapes all data into a file and moves it to the inbox on success.
    """
    if not retailer_store_id:
        return False

    output = ScraperOutput(command, company, store_name)
    jsonl_writer = JsonlWriter(company, store_name_slug, state)
    scrape_successful = False

    try:
        session = requests.Session()
        session.headers.update({
            "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
            "x-shopping-mode": "11111111-1111-1111-1111-111111111111"
        })
        session.cookies.set("iga-shop.retailerStoreId", retailer_store_id)

        try:
            session.get("https://www.igashop.com.au/", timeout=60)
        except requests.exceptions.RequestException:
            return False

        session_id = str(uuid.uuid4())
        categories_to_fetch = get_iga_categories(command, retailer_store_id, session)
        if not categories_to_fetch:
            return False

        total_categories = len(categories_to_fetch)
        output.update_progress(total_categories=total_categories)
        jsonl_writer.open()

        for i, category_data in enumerate(categories_to_fetch):
            output.update_progress(categories_scraped=i + 1)
            category_identifier = category_data['identifier']
            
            take = 36
            skip = 0
            previous_page_skus = set()

            while True:
                api_url = f"https://www.igashop.com.au/api/storefront/stores/{retailer_store_id}/categories/{requests.utils.quote(category_identifier)}/search"
                params = {'take': take, 'skip': skip, 'sessionId': session_id}

                try:
                    response = session.get(api_url, params=params, timeout=60)
                    if response.status_code == 404:
                        break
                    response.raise_for_status()
                    data = response.json()
                    
                    raw_products_on_page = data.get("items", [])
                    if not raw_products_on_page:
                        break

                    current_page_skus = {p.get('sku') for p in raw_products_on_page}
                    if current_page_skus == previous_page_skus:
                        break
                    previous_page_skus = current_page_skus

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_iga(
                        raw_product_list=raw_products_on_page, company=company,
                        store_id=store_id, store_name=store_name, state=state, timestamp=scrape_timestamp
                    )
                    
                    new_products_count = 0
                    duplicate_products_count = 0
                    metadata_for_jsonl = data_packet.get('metadata', {})
                    for product in data_packet.get('products', []):
                        if jsonl_writer.write_product(product, metadata_for_jsonl):
                            new_products_count += 1
                        else:
                            duplicate_products_count += 1
                    
                    output.update_progress(new_products=new_products_count, duplicate_products=duplicate_products_count)

                except (requests.exceptions.RequestException, json.JSONDecodeError):
                    raise

                time.sleep(random.uniform(0.5, 1.5))
                skip += take

        scrape_successful = True

    finally:
        jsonl_writer.finalize(scrape_successful)
        output.finalize()

    return scrape_successful