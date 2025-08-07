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
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles

def scrape_and_save_coles_data(company: str, store: str, categories_to_fetch: list, save_path: str, store_id: str = None):
    """
    Launches a browser for initial session setup, then uses a lightweight
    requests session to iterate through categories and save product data.
    """
    print(f"--- Initializing Coles Scraper for {company} ({store}) ---")
    if store_id:
        print(f"Targeting specific store ID: {store_id}")

    progress_file_path = os.path.join(save_path, f"coles_progress_{store_id or 'national'}.json")

    # --- Load Progress ---
    completed_categories = []
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            try:
                completed_categories = json.load(f)
            except json.JSONDecodeError:
                completed_categories = []

    # --- Selenium Phase: Session Initialization ---
    driver = None
    try:
        print("--- Selenium Phase: Initializing browser for session ---")
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get("https://www.coles.com.au")
        
        # Set the fulfillment store cookie if a specific store is targeted
        if store_id:
            print(f"Setting fulfillment cookie for store ID: {store_id}")
            # The cookie needs to be set on the correct domain.
            # Visiting the site first ensures the domain is correct.
            driver.add_cookie({"name": "fulfillmentStoreId", "value": str(store_id)})
            driver.refresh() # Refresh to apply the new store context

        input("ACTION REQUIRED: Please solve any CAPTCHA, then press Enter here to continue...")

        print("\nGiving you 15 seconds to visually confirm the store on the homepage...")
        time.sleep(15)

        # --- Requests Phase: Data Scraping ---
        print("\n--- Requests Phase: Transferring session to scrape data ---")
        
        # Create a requests session and transfer cookies
        session = requests.Session()
        session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        print("Selenium browser is no longer needed. Closing it.")
        driver.quit()
        driver = None # Ensure driver is not used beyond this point

        for category in categories_to_fetch:
            if category in completed_categories:
                print(f"Skipping already completed category: {category}")
                continue

            print(f"\n--- Scraping Category: {category} ---")
            page_num = 1
            total_pages = 1 # Will be updated after the first successful request
            
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
                    search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                    raw_product_list = search_results.get("results", [])

                    if not raw_product_list and page_num > 1:
                        print("No more products found for this category.")
                        break

                    # Update total pages on the first request
                    if page_num == 1:
                        total_results = search_results.get("noOfResults", 0)
                        page_size = search_results.get("pageSize", 48)
                        if total_results > 0 and page_size > 0:
                            total_pages = math.ceil(total_results / page_size)
                        print(f"Category has {total_results} products across {total_pages} pages.")

                    scrape_timestamp = datetime.now()
                    # Use the specific store_id for cleaning if provided, otherwise use the generic store name
                    store_identifier = store_id if store_id else store
                    data_packet = clean_raw_data_coles(raw_product_list, company, store_identifier, category, page_num, scrape_timestamp)
                    
                    if data_packet['products']:
                        print(f"Found and cleaned {len(data_packet['products'])} products.")
                        
                        file_name = f"{company.lower()}_{store_identifier}_{category}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                        file_path = os.path.join(save_path, file_name)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data_packet, f, indent=4)
                        print(f"Successfully saved cleaned data to {file_name}")
                    else:
                        print("No products found on this page.")

                except requests.exceptions.RequestException as e:
                    print(f"ERROR: Network request failed on page {page_num} for '{category}': {e}")
                    print("Skipping to the next category.")
                    break # Exit category loop on network error
                except Exception as e:
                    print(f"ERROR: An unexpected error occurred on page {page_num} for '{category}': {e}")
                    break # Exit category loop on other errors
                
                page_num += 1
                time.sleep(1) # Be respectful to the server

            # Mark category as complete
            completed_categories.append(category)
            with open(progress_file_path, 'w') as f:
                json.dump(completed_categories, f, indent=4)
            print(f"Finished category: {category}")

        print("\n--- All categories processed ---")
        if os.path.exists(progress_file_path):
            os.remove(progress_file_path)

    except Exception as e:
        print(f"\nA critical error occurred: {e}")
        print("The scraping process was interrupted.")
    
    finally:
        if driver:
            print("Closing any remaining Selenium browser.")
            driver.quit()

