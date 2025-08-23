import json
import time
import os
from datetime import datetime
import math
import requests
from bs4 import BeautifulSoup
from django.utils.text import slugify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Added this line
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles
from api.utils.scraper_utils.jsonl_writer import JsonlWriter

def scrape_and_save_coles_data(company: str, store_id: str, store_name: str, state: str, categories_to_fetch: list):
    """
    Launches a browser for session setup, then uses a requests session to scrape data.
    Includes a verification step and uses the central checkpoint manager for progress.
    """
    # The store_id from the database is prefixed (e.g., 'COL:1234').
    # We need the numeric part for the fulfillment cookie.
    numeric_store_id = store_id.split(':')[-1] if store_id and ':' in store_id else store_id
    
    # Use the numeric ID for the slug to keep it clean
    store_name_slug = f"{slugify(store_name)}-{numeric_store_id}"
    print(f"--- Initializing Hybrid Coles Scraper for store: {store_name} ({store_name_slug}) ---")

    scrape_successful = False
    jsonl_writer = JsonlWriter(company, store_name_slug, state)

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
        print(f"Setting fulfillment cookie for store ID: {numeric_store_id}")
        driver.add_cookie({"name": "fulfillmentStoreId", "value": str(numeric_store_id)})
        print("Refreshing the page to apply the new store context.")
        driver.refresh()

        print("ACTION REQUIRED: Please solve any CAPTCHA in the browser.")
        print("Waiting for __NEXT_DATA__ script to appear (indicating main page load)...")
        
        timeout_seconds = 300 # 5 minutes timeout for CAPTCHA
        
        try:
            # Wait until the __NEXT_DATA__ script tag is present
            WebDriverWait(driver, timeout_seconds, poll_frequency=2).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
            print("__NEXT_DATA__ script found. CAPTCHA appears to be solved.")
        except TimeoutException:
            print("Timeout reached. __NEXT_DATA__ script did not appear within the allotted time.")
            raise Exception("CAPTCHA not solved or main page did not load within the allotted time.")

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

    try:
        jsonl_writer.open()

        # --- Main Scraping Loop ---
        for category_slug in categories_to_fetch:
            print(f"\n--- Scraping Category: {category_slug} ---")
            page_num = 1
            total_pages = 1

            category_successfully_completed = False
            while True: # Will break out internally
                if page_num > total_pages and total_pages > 1:
                    category_successfully_completed = True
                    break

                browse_url = f"https://www.coles.com.au/browse/{category_slug}?page={page_num}"
                
                try:
                    print(f"Requesting page {page_num}/{total_pages if total_pages > 1 else '?'}")
                    response = session.get(browse_url, timeout=30)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, 'html.parser')
                    json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
                    
                    if not json_element:
                        print(f"ERROR: Could not find __NEXT_DATA__ on page {page_num} for '{category_slug}'. Skipping category.")
                        break

                    full_data = json.loads(json_element.string)

                    if page_num == 1:
                        try:
                            actual_store_id = full_data.get("props", {}).get("pageProps", {}).get("initStoreId")
                            print(f"Verifying store ID for category '{category_slug}'...")
                            if str(actual_store_id) == str(numeric_store_id):
                                print(f"SUCCESS: Store ID {actual_store_id} matches target {numeric_store_id}.")
                            else:
                                print(f"ERROR: Store ID mismatch! Expected {numeric_store_id}, but page data shows {actual_store_id}. Skipping category.")
                                break 
                        except (KeyError, TypeError) as e:
                            print(f"ERROR: Could not find storeId in page data for verification: {e}. Skipping category.")
                            break
                    
                    search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                    raw_product_list = search_results.get("results", [])

                    if not raw_product_list:
                        print("No more products found for this category.")
                        category_successfully_completed = True
                        break

                    if page_num == 1:
                        total_results = search_results.get("noOfResults", 0)
                        page_size = search_results.get("pageSize", 48)
                        if total_results > 0 and page_size > 0:
                            total_pages = math.ceil(total_results / page_size)
                        print(f"Category has {total_results} products across {total_pages} pages.")

                    scrape_timestamp = datetime.now()
                    data_packet = clean_raw_data_coles(raw_product_list, company, store_id, store_name, state, category_slug, page_num, scrape_timestamp)
                    
                    if data_packet['products']:
                        print(f"Found and cleaned {len(data_packet['products'])} products.")
                        
                        products_on_page = data_packet.get('products', [])
                        metadata = data_packet.get('metadata', {})
                        
                        products_written_count = 0
                        for product in products_on_page:
                            if jsonl_writer.write_product(product, metadata):
                                products_written_count += 1
                        
                        print(f"Successfully saved {products_written_count}/{len(products_on_page)} products to the inbox.")

                except requests.exceptions.RequestException as e:
                    print(f"ERROR: Network request failed on page {page_num} for '{category_slug}': {e}")
                    break 
                except Exception as e:
                    print(f"ERROR: An unexpected error occurred on page {page_num} for '{category_slug}': {e}")
                    break
                
                page_num += 1

        scrape_successful = True
        print("\n--- All categories processed for this store ---")
    finally:
        jsonl_writer.finalize(scrape_successful)