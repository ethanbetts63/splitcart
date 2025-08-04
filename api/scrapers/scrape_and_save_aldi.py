import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_aldi import clean_raw_data_aldi
from api.utils.scraper_utils.checkpoint_manager import read_checkpoint, update_page_progress, mark_category_complete, clear_checkpoint

def scrape_and_save_aldi_data(company: str, store_name: str, store_id: str, categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper for a specific ALDI store with checkpointing.
    """
    print(f"--- Initializing ALDI Scraper for {company} ({store_name}) ---")

    # --- Checkpoint Initialization ---
    progress = read_checkpoint(company)
    completed_categories = progress.get("completed_categories", [])

    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    for category_slug, category_key in categories_to_fetch:
        if category_slug in completed_categories:
            print(f"Skipping already completed category: '{category_slug}'")
            continue

        print(f"\n--- Starting category: '{category_slug}' ---")
        
        limit = 30
        page_num = 1
        offset = 0

        if progress.get("current_category") == category_slug:
            page_num = progress.get("last_completed_page", 0) + 1
            offset = (page_num - 1) * limit
            print(f"Resuming category '{category_slug}' from page {page_num} (offset: {offset}).")

        category_successfully_completed = False
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
                    category_successfully_completed = True
                    break
                response.raise_for_status()
                data = response.json()
                
                raw_products_on_page = data.get("data", [])

                if not raw_products_on_page:
                    print(f"Page {page_num} is empty. Assuming end of category '{category_slug}'.")
                    category_successfully_completed = True
                    break

                scrape_timestamp = datetime.now()
                data_packet = clean_raw_data_aldi(
                    raw_product_list=raw_products_on_page, company=company, store=store_name,
                    category_slug=category_slug, page_num=page_num, timestamp=scrape_timestamp
                )
                print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                file_name = f"{company}_{store_name}_{category_slug.replace('/', '_')}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                file_path = os.path.join(save_path, file_name)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_packet, f, indent=4)
                print(f"Successfully saved cleaned data to {file_name}")

                # --- Checkpoint: Update Page Progress ---
                update_page_progress(
                    company_name=company, store=store_name,
                    completed_cats=completed_categories,
                    current_cat=category_slug, page_num=page_num
                )

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed on page {page_num} for '{category_slug}': {e}")
                break
            except json.JSONDecodeError:
                print(f"ERROR: Failed to decode JSON on page {page_num} for '{category_slug}'.")
                break

            sleep_time = random.uniform(2, 5)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
            offset += limit
            page_num += 1
        
        if category_successfully_completed:
            completed_categories.append(category_slug)
            mark_category_complete(
                company_name=company, store=store_name,
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
        print(f"\n--- ALDI scraper for store '{store_name}' finished, but not all categories were completed. Checkpoint retained. ---")

