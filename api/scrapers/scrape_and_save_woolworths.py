import requests
import json
import time
import random
import os
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths
from api.utils.scraper_utils.checkpoint_utils import read_checkpoint, update_page_progress, mark_category_complete, clear_checkpoint

def scrape_and_save_woolworths_data(company: str, store_name: str, store_id: str, categories_to_fetch: list, save_path: str):
    """
    Launches a requests-based scraper for a specific Woolworths store with checkpointing.
    """
    print(f"--- Initializing Woolworths Scraper for {company} ({store_name}) ---")

    # --- Checkpoint Initialization ---
    progress = read_checkpoint(company)
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
                    company=company, store=store_name, category=category_slug,
                    page_num=page_num, timestamp=scrape_timestamp
                )
                print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                file_name = f"{company.lower()}_{store_name.lower()}_{category_slug}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
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

            sleep_time = random.uniform(2, 4)
            print(f"Waiting for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            
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
        print(f"\n--- Woolworths scraper for store '{store_name}' finished, but not all categories were completed. Checkpoint retained. ---")

