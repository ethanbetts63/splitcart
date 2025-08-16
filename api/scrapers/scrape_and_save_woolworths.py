import requests
import json
import time
import random
import os
from datetime import datetime
from django.utils.text import slugify
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths
from api.utils.scraper_utils.checkpoint_utils.read_checkpoint import read_checkpoint
from api.utils.scraper_utils.checkpoint_utils.update_page_progress import update_page_progress
from api.utils.scraper_utils.checkpoint_utils.mark_category_complete import mark_category_complete
from api.utils.scraper_utils.checkpoint_utils.clear_checkpoint import clear_checkpoint

def scrape_and_save_woolworths_data(company: str, state: str, stores: list, categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper for a specific Woolworths store with checkpointing.
    """
    print(f"--- Initializing Woolworths Scraper for {company} in {state} ---")

    for store in stores:
        store_name = store.get("store_name")
        store_id = store.get("store_id")

        print(f"--- Initializing Woolworths Scraper for {company} ({store_name}) ---")

        # --- Checkpoint Initialization ---
        progress = read_checkpoint(company)
        
        store_name_slug = f"{slugify(store_name)}-{store_id}"

        # Check if we are starting a new store or resuming an old one
        start_scraping_fresh = not progress.get("current_store") or progress.get("current_store") != store_name_slug
        if start_scraping_fresh:
            print(f"Starting fresh scrape for {store_name}. Checkpoint from previous store will be ignored for this run.")
            completed_categories = []
        else:
            print(f"Resuming scrape for {store_name}.")
            completed_categories = progress.get("completed_categories", [])
        
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

        for category_slug, category_id in categories_to_fetch:
            if category_slug in completed_categories:
                print(f"Skipping already completed category: '{category_slug}'")
                continue

            print(f"\n--- Starting category: '{category_slug}' ---")
            
            page_num = 1
            if progress.get("current_category") == category_slug:
                page_num = progress.get("last_completed_page", 0) + 1
                print(f"Resuming category '{category_slug}' from page {page_num}.")

            category_successfully_completed = False
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
                        category_successfully_completed = True
                        break

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_woolworths(
                        raw_product_list=raw_products_on_page,
                        company=company, store_id=store_id, store_name=store_name, state=state, category=category_slug,
                        page_num=page_num, timestamp=scrape_timestamp
                    )
                    print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                    file_name = f"{slugify(company)}_{slugify(store_name)}_{category_slug}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data_packet, f, indent=4)
                    print(f"Successfully saved cleaned data to {file_name}")

                    # --- Checkpoint: Update Page Progress ---
                    update_page_progress(
                        company_name=company, store=store_name_slug,
                        completed_cats=completed_categories,
                        current_cat=category_slug, page_num=page_num
                    )

                except requests.exceptions.RequestException as e:
                    print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                    break
                except json.JSONDecodeError:
                    print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'.")
                    break

                sleep_time = random.uniform(0.5, 1)
                print(f"Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
                
                page_num += 1
            
            if category_successfully_completed:
                completed_categories.append(category_slug)
                mark_category_complete(
                    company_name=company, store=store_name_slug,
                    completed_cats=completed_categories,
                    new_completed_cat=category_slug
                )
                print(f"--- Finished category: '{category_slug}' ---")
            else:
                print(f"--- Paused category: '{category_slug}'. Progress saved. ---")

        all_category_slugs = [cat[0] for cat in categories_to_fetch]
        if all(cat in completed_categories for cat in all_category_slugs):
            print(f"\n--- All categories for '{store_name}' scraped successfully. Clearing checkpoint. ---")
            clear_checkpoint(company)
        else:
            print(f"\n--- Woolworths scraper for store '{store_name}' finished, but not all categories were completed. Checkpoint retained. ---")

