import json
import re
import time
import random
import math
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.utils.clean_raw_data_coles import clean_raw_data_coles

def scrape_and_save_coles_data(categories_to_fetch: list, save_path: str):
    """
    Launches a browser, handles CAPTCHA, then iterates through all pages of
    the given categories, saving each page's cleaned product data to a file.
    """
    print("--- Initializing Coles Scraper Tool ---")
    progress_file_path = os.path.join(save_path, "coles_progress.json")

    while True:
        driver = None
        
        # Load progress
        completed_categories = []
        in_progress_category = {}
        if os.path.exists(progress_file_path):
            with open(progress_file_path, 'r') as f:
                try:
                    progress_data = json.load(f)
                    # Handle both old (list) and new (dict) formats
                    if isinstance(progress_data, list):
                        completed_categories = progress_data
                        in_progress_category = {}
                        print("Detected old progress file format. Converting.")
                    else:
                        completed_categories = progress_data.get("completed", [])
                        in_progress_category = progress_data.get("in_progress", {})
                except json.JSONDecodeError:
                    print("Could not decode progress file. Starting fresh.")
                    completed_categories = []
                    in_progress_category = {}

            print(f"Loaded {len(completed_categories)} completed categories from progress file.")
            if in_progress_category:
                print(f"Resuming with category '{in_progress_category.get('name')}' from page {in_progress_category.get('next_page')}.")

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

            url = "https://www.coles.com.au"
            print(f"Navigating to {url}...")
            driver.get(url)

            print("\n" + "="*50)
            print("ACTION REQUIRED: The browser has opened.")
            print("Please solve the CAPTCHA or any security check now.")
            input("Once you are on the main Coles homepage, press Enter here to continue...")
            print("="*50 + "\n")
            print("Resuming script...")

            page_title = driver.title
            if "Coles" not in page_title:
                print("\nFAILURE: Could not get to the main Coles website. Exiting scraper.")
                if driver:
                    driver.quit()
                continue # Restart the loop to try again
            print("SUCCESS: Security passed.\n")

            for category in categories_to_fetch:
                if category in completed_categories:
                    print(f"--- Skipping already completed category: '{category}' ---\n")
                    continue

                
                resuming = in_progress_category and in_progress_category.get("name") == category
                page_num = 1
                total_pages = 1

                if resuming:
                    print(f"--- Resuming category: '{category}' ---")
                    page_num = in_progress_category.get("next_page", 1)
                    total_pages = page_num # Temporarily set to allow loop entry
                else:
                    print(f"--- Starting category: '{category}' ---")

                category_succeeded = False
                
                while page_num <= total_pages:
                    print(f"Navigating to page {page_num} of {total_pages} for '{category}'...")
                    browse_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
                    driver.get(browse_url)

                    if "This content is blocked" in driver.page_source or "Access Denied" in driver.title:
                        print(f"BLOCK DETECTED: Scraper was blocked on page {page_num} of '{category}'. Restarting...")
                        raise Exception("Blocked by website.")
                    
                    try:
                        wait = WebDriverWait(driver, 10)
                        json_element = wait.until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
                        
                        full_json_text = json_element.get_attribute('innerHTML')
                        full_data = json.loads(full_json_text)
                        
                        search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                        raw_product_list = search_results.get("results", [])

                        if not raw_product_list:
                            print(f"WARNING: Product list was empty for page {page_num} of '{category}'. Stopping this category.")
                            break

                        if resuming or page_num == 1:
                            total_results = search_results.get("noOfResults", 0)
                            page_size = search_results.get("pageSize", 48)
                            if total_results > 0 and page_size > 0:
                                total_pages = math.ceil(total_results / page_size)
                                print(f"Found {total_results} products across {total_pages} pages for '{category}'.")
                            # After resuming, we don't want this to trigger on every page
                            resuming = False

                        scrape_timestamp = datetime.now()
                        data_packet = clean_raw_data_coles(raw_product_list, category, page_num, scrape_timestamp)
                        print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                        file_name = f"coles_{category}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                        file_path = os.path.join(save_path, file_name)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data_packet, f, indent=4)
                        print(f"Successfully saved cleaned data to {file_name}")

                        # Update progress file after each successful page
                        progress = {
                            "completed": completed_categories,
                            "in_progress": {"name": category, "next_page": page_num + 1}
                        }
                        with open(progress_file_path, 'w') as f:
                            json.dump(progress, f, indent=4)

                    except Exception as e:
                        print(f"ERROR: Failed on page {page_num} for '{category}'. Details: {e}")
                        break

                    # sleep_time = random.uniform(1, 2)
                    # print(f"Waiting for {sleep_time:.2f} seconds before next page...")
                    # time.sleep(sleep_time)
                    
                    page_num += 1
                
                if page_num > total_pages:
                    category_succeeded = True

                if category_succeeded:
                    print(f"--- Finished category: '{category}' ---")
                    completed_categories.append(category)
                    in_progress_category = {} # Clear in_progress
                    progress = {
                        "completed": completed_categories,
                        "in_progress": in_progress_category
                    }
                    with open(progress_file_path, 'w') as f:
                        json.dump(progress, f, indent=4)
                    print(f"Saved progress. {len(completed_categories)} of {len(categories_to_fetch)} categories complete.\n")
                else:
                    print(f"--- Incomplete category: '{category}'. Will retry on next run. ---\n")
                    break # Exit the category loop and trigger a restart

            if len(completed_categories) == len(categories_to_fetch):
                print("All categories scraped successfully!")
                if os.path.exists(progress_file_path):
                    os.remove(progress_file_path)
                    print("Progress file removed.")
                break

        except Exception as e:
            print(f"\nA critical error occurred during scraping: {e}")
        
        finally:
            if driver:
                print("\n--- Scraper tool finished, closing browser. ---")
                driver.quit()

        if len(completed_categories) < len(categories_to_fetch):
            print("Restarting scraper due to interruption or incomplete categories...")
        else:
            break