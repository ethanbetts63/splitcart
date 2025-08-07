import json
import time
import os
from datetime import datetime
import math
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles

def scrape_and_save_coles_data(company: str, store_name: str, categories_to_fetch: list, save_path: str, store_id: str):
    """
    Launches a browser for session setup, then uses a requests session to scrape data.
    Includes a verification step on the first page of each category.
    """
    print(f"--- Initializing Hybrid Coles Scraper for store: {store_name} ({store_id}) ---")
    progress_file_path = os.path.join(save_path, f"coles_progress_{store_id}.json")

    # --- Load Progress ---
    completed_categories = []
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            try:
                # Handle both old dict format and new list format for progress
                progress_data = json.load(f)
                if isinstance(progress_data, list):
                    completed_categories = progress_data
                elif isinstance(progress_data, dict):
                    completed_categories = progress_data.get("completed", [])
                else:
                    completed_categories = []
            except json.JSONDecodeError:
                completed_categories = []

    # --- Selenium Phase: Session Initialization ---
    driver = None
    session = None
    try:
        print("--- Selenium Phase: Initializing browser for session ---")
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get("https://www.coles.com.au")
        
        print("Clearing all cookies to ensure a clean session.")
        driver.delete_all_cookies()
        print(f"Setting fulfillment cookie for store ID: {store_id}")
        driver.add_cookie({"name": "fulfillmentStoreId", "value": str(store_id)})
        print("Refreshing the page to apply the new store context.")
        driver.refresh()

        input("ACTION REQUIRED: Please solve any CAPTCHA, then press Enter here to continue...")

        # --- Requests Phase: Data Scraping ---
        print("\n--- Requests Phase: Transferring session to scrape data ---")
        session = requests.Session()
        session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        print("Selenium browser is no longer needed. Closing it.")
        driver.quit()
        driver = None

    except Exception as e:
        print(f"\nA critical error occurred during the Selenium phase: {e}")
        if driver:
            driver.quit()
        return # Exit if selenium phase fails

    if not session:
        print("ERROR: Requests session was not created. Aborting.")
        return

    # --- Main Scraping Loop ---
    for category in categories_to_fetch:
        if category in completed_categories:
            print(f"Skipping already completed category: {category}")
            continue

        print(f"\n--- Scraping Category: {category} ---")
        page_num = 1
        total_pages = 1
        
        while page_num <= total_pages:
            browse_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
            
            try:
                print(f"Requesting page {page_num}/{total_pages if total_pages > 1 else '?'}")
                response = session.get(browse_url, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                
                if not json_element:
                    print(f"ERROR: Could not find __NEXT_DATA__ on page {page_num} for '{category}'. Skipping category.")
                    break

                full_data = json.loads(json_element.string)

                # --- VERIFICATION STEP (only on page 1) ---
                if page_num == 1:
                    try:
                        actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                        print(f"Verifying store ID for category '{category}'...")
                        if str(actual_store_id) == str(store_id):
                            print(f"SUCCESS: Store ID {actual_store_id} matches target {store_id}.")
                        else:
                            print(f"ERROR: Store ID mismatch! Expected {store_id}, but page data shows {actual_store_id}. Skipping category.")
                            # Save the problematic JSON for debugging
                            debug_file_path = os.path.join(save_path, '__NEXT_DATA___debug.json')
                            with open(debug_file_path, 'w', encoding='utf-8') as f:
                                json.dump(full_data, f, indent=4)
                            print(f"Saved the __NEXT_DATA__ block to {debug_file_path} for inspection.")
                            break 
                    except (KeyError, TypeError) as e:
                        print(f"ERROR: Could not find storeId in page data for verification: {e}. Skipping category.")
                        break
                
                search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                raw_product_list = search_results.get("results", [])

                if not raw_product_list and page_num > 1:
                    print("No more products found for this category.")
                    break

                if page_num == 1:
                    total_results = search_results.get("noOfResults", 0)
                    page_size = search_results.get("pageSize", 48)
                    if total_results > 0 and page_size > 0:
                        total_pages = math.ceil(total_results / page_size)
                    print(f"Category has {total_results} products across {total_pages} pages.")

                scrape_timestamp = datetime.now()
                data_packet = clean_raw_data_coles(raw_product_list, company, store_id, category, page_num, scrape_timestamp)
                
                if data_packet['products']:
                    print(f"Found and cleaned {len(data_packet['products'])} products.")
                    file_name = f"{company.lower()}_{store_id}_{category}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data_packet, f, indent=4)
                    print(f"Successfully saved cleaned data to {file_name}")

            except requests.exceptions.RequestException as e:
                print(f"ERROR: Network request failed on page {page_num} for '{category}': {e}")
                break 
            except Exception as e:
                print(f"ERROR: An unexpected error occurred on page {page_num} for '{category}': {e}")
                break
            
            page_num += 1
            time.sleep(1)

        completed_categories.append(category)
        with open(progress_file_path, 'w') as f:
            json.dump(completed_categories, f, indent=4)
        print(f"Finished or skipped category: {category}")

    print("\n--- All categories processed ---")
    if os.path.exists(progress_file_path):
        os.remove(progress_file_path)
