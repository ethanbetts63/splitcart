import json
import time
import os
from datetime import datetime
import math
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from api.utils.scraper_utils.clean_raw_data_coles import clean_raw_data_coles

# CHANGE 1: Function signature updated to accept company and store
def scrape_and_save_coles_data(company: str, store: str, categories_to_fetch: list, save_path: str):
    """
    Launches a browser, handles CAPTCHA, then iterates through all pages of
    the given categories, saving each page's cleaned product data to a file.
    """
    print(f"--- Initializing coles Scraper Tool for {company} ({store}) ---")
    progress_file_path = os.path.join(save_path, "coles_progress.json")

    # --- NO CHANGES TO THE CORE LOGIC BELOW ---
    while True:
        driver = None
        
        completed_categories = []
        in_progress_category = {}
        if os.path.exists(progress_file_path):
            with open(progress_file_path, 'r') as f:
                try:
                    progress_data = json.load(f)
                    if isinstance(progress_data, list):
                        completed_categories = progress_data
                        in_progress_category = {}
                    else:
                        completed_categories = progress_data.get("completed", [])
                        in_progress_category = progress_data.get("in_progress", {})
                except json.JSONDecodeError:
                    completed_categories = []
                    in_progress_category = {}

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("user-agent=SplitCartScraper/1.0 (Contact: admin@splitcart.com)")
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            driver.get("https://www.coles.com.au")

            input("ACTION REQUIRED: Please solve the CAPTCHA, then press Enter here to continue...")
            
            for category in categories_to_fetch:
                if category in completed_categories:
                    continue

                resuming = in_progress_category and in_progress_category.get("name") == category
                page_num = 1
                total_pages = 1

                if resuming:
                    page_num = in_progress_category.get("next_page", 1)
                    total_pages = page_num
                
                category_succeeded = False
                
                while page_num <= total_pages:
                    browse_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
                    driver.get(browse_url)
                    
                    try:
                        wait = WebDriverWait(driver, 10)
                        json_element = wait.until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
                        full_data = json.loads(json_element.get_attribute('innerHTML'))
                        
                        search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                        raw_product_list = search_results.get("results", [])

                        if not raw_product_list:
                            break

                        if resuming or page_num == 1:
                            total_results = search_results.get("noOfResults", 0)
                            page_size = search_results.get("pageSize", 48)
                            if total_results > 0 and page_size > 0:
                                total_pages = math.ceil(total_results / page_size)
                            resuming = False

                        scrape_timestamp = datetime.now()
                        # CHANGE 2: Pass company and store to the cleaner
                        data_packet = clean_raw_data_coles(raw_product_list, company, store, category, page_num, scrape_timestamp)
                        print(f"Found and cleaned {len(data_packet['products'])} products on page {page_num}.")

                        # CHANGE 3: Update filename format
                        file_name = f"{company.lower()}_{store.lower()}_{category}_page-{page_num}_{scrape_timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                        file_path = os.path.join(save_path, file_name)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data_packet, f, indent=4)
                        print(f"Successfully saved cleaned data to {file_name}")

                        progress = {"completed": completed_categories, "in_progress": {"name": category, "next_page": page_num + 1}}
                        with open(progress_file_path, 'w') as f:
                            json.dump(progress, f, indent=4)

                    except Exception as e:
                        print(f"ERROR: Failed on page {page_num} for '{category}'. Details: {e}")
                        break
                    
                    page_num += 1
                
                if page_num > total_pages:
                    category_succeeded = True

                if category_succeeded:
                    completed_categories.append(category)
                    progress = {"completed": completed_categories, "in_progress": {}}
                    with open(progress_file_path, 'w') as f:
                        json.dump(progress, f, indent=4)

            if len(completed_categories) == len(categories_to_fetch):
                if os.path.exists(progress_file_path):
                    os.remove(progress_file_path)
                break

        except Exception as e:
            print(f"\nA critical error occurred during scraping: {e}")
        
        finally:
            if driver:
                driver.quit()

        if len(completed_categories) < len(categories_to_fetch):
            print("Restarting scraper...")
        else:
            break
