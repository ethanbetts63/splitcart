import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_iga import clean_raw_data_iga
from api.utils.scraper_utils.get_iga_categories import get_iga_categories
from api.utils.scraper_utils.checkpoint_manager import read_checkpoint, update_page_progress, mark_category_complete, clear_checkpoint

def scrape_and_save_iga_data(company: str, store_id: str, store_name: str, store_name_slug: str, state: str, save_path: str):
    """
    Launches a requests-based scraper for IGA with checkpointing.
    """
    print("--- Initializing IGA Scraper Tool ---")

    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    # --- Checkpoint Initialization ---
    progress = read_checkpoint(company)
    
    start_scraping = False
    if not progress.get("current_store") or progress.get("current_store") != store_name_slug:
        start_scraping = True

    print(f"\n--- Starting Store: {store_name} (ID: {store_id}) ---")

    categories_to_fetch = get_iga_categories(store_id, session)
    if not categories_to_fetch:
        print(f"Could not retrieve categories for {store_name}. Skipping.")
        return

    completed_categories = progress.get("completed_categories", []) if not start_scraping else []

    for category_name in categories_to_fetch:
        category_slug = category_name.lower().replace(' & ', '-').replace(' ', '-').replace(',', '')
        if category_slug in completed_categories:
            print(f"  Skipping already completed category: '{category_name}'")
            continue

        print(f"  -- Starting category: '{category_name}' --")
        
        take = 36
        page_num = 1
        skip = 0

        if not start_scraping and progress.get("current_category") == category_slug:
            page_num = progress.get("last_completed_page", 0) + 1
            skip = (page_num - 1) * take
            print(f"    Resuming category '{category_name}' from page {page_num}.")

        previous_page_skus = set()
        category_successfully_completed = False
        while True:
            print(f"    Attempting to fetch page {page_num} for '{category_name}' (skip: {skip})...")
            
            api_url = f"https://www.igashop.com.au/api/storefront/stores/{store_id}/categories/{requests.utils.quote(category_name)}/search"
            params = {'take': take, 'skip': skip}

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
                    category_successfully_completed = True
                    break

                current_page_skus = {p.get('sku') for p in raw_products_on_page}
                if current_page_skus == previous_page_skus:
                    print(f"    WARNING: Duplicate products detected. Stopping category.")
                    category_successfully_completed = True
                    break
                previous_page_skus = current_page_skus

                scrape_timestamp = datetime.now()
                data_packet = clean_raw_data_iga(
                    raw_product_list=raw_products_on_page, company=company,
                    store_id=store_id, store_name=store_name, state=state,
                    category_slug=category_slug, page_num=page_num, timestamp=scrape_timestamp
                )
                print(f"    Found and cleaned {len(data_packet['products'])} products.")

                file_name = f"{company}_{store_name_slug}_{category_slug}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_packet, f, indent=4)
                print(f"    Successfully saved cleaned data to {file_name}")

                update_page_progress(
                    company_name=company, store=store_name_slug,
                    completed_cats=completed_categories,
                    current_cat=category_slug, page_num=page_num
                )

            except requests.exceptions.RequestException as e:
                print(f"    ERROR: Request failed: {e}")
                break
            except json.JSONDecodeError:
                print(f"    ERROR: Failed to decode JSON.")
                break

            sleep_time = random.uniform(2, 4)
            print(f"    Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            skip += take
            page_num += 1
        
        if category_successfully_completed:
            completed_categories.append(category_slug)
            mark_category_complete(
                company_name=company, store=store_name_slug,
                completed_cats=completed_categories,
                new_completed_cat=category_slug
            )
            print(f"  -- Finished category: '{category_name}' --")
        else:
            print(f"  -- Paused category: '{category_name}'. Progress saved. ---")

    print("\n--- IGA scraper tool finished for this store. ---")
    clear_checkpoint(company)

