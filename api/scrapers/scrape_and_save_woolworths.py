import requests
import json
import time
import random
from datetime import datetime
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths
from api.utils.scraper_utils.jsonl_writer import JsonlWriter
from api.utils.scraper_utils.output_utils import ScraperOutput

def scrape_and_save_woolworths_data(command, company: str, state: str, stores: list, categories_to_fetch: list):
    """
    Launches a requests-based scraper for a specific Woolworths store.
    Scrapes all data into a file and moves it to the inbox on success.
    """
    for store in stores:
        store_name = store.get("store_name")
        store_id = store.get("store_id")
        store_name_slug = f"{slugify(store_name)}-{store_id}"
        
        output = ScraperOutput(command, company, store_name)
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
                session.get("https://www.woolworths.com.au/", timeout=60)
            except requests.exceptions.RequestException as e:
                return

            jsonl_writer.open()
            total_categories = len(categories_to_fetch)
            output.update_progress(total_categories=total_categories)

            for i, (category_slug, category_id) in enumerate(categories_to_fetch):
                output.update_progress(categories_scraped=i + 1)
                
                page_num = 1
                while True:
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
                            break

                        scrape_timestamp = datetime.now()
                        data_packet = clean_raw_data_woolworths(
                            raw_product_list=raw_products_on_page,
                            company=company, store_id=store_id, store_name=store_name, state=state, timestamp=scrape_timestamp
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
                        break
                    
                    page_num += 1

            scrape_successful = True

        finally:
            jsonl_writer.finalize(scrape_successful)
            output.finalize()