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
    driver = None

    try:
        # --- Set up and launch the visible browser with stealth options ---
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
        
        # --- THE FIX: Restore the anti-detection options ---
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # --- Navigate and pause for manual CAPTCHA solving ---
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
            return
        print("SUCCESS: Security passed.\n")

        # --- Loop through categories and fetch data from the page source ---
        for category in categories_to_fetch:
            print(f"--- Starting category: '{category}' ---")
            
            page_num = 1
            total_pages = 1
            
            while page_num <= total_pages:
                print(f"Navigating to page {page_num} of {total_pages} for '{category}'...")
                browse_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
                driver.get(browse_url)
                
                try:
                    time.sleep(3)

                    wait = WebDriverWait(driver, 10)
                    json_element = wait.until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
                    
                    full_json_text = json_element.get_attribute('innerHTML')
                    full_data = json.loads(full_json_text)
                    
                    search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                    raw_product_list = search_results.get("results", [])

                    if not raw_product_list:
                        print(f"WARNING: Product list was empty for page {page_num} of '{category}'. Stopping this category.")
                        break

                    if page_num == 1:
                        total_results = search_results.get("noOfResults", 0)
                        page_size = search_results.get("pageSize", 48)
                        if total_results > 0 and page_size > 0:
                            total_pages = math.ceil(total_results / page_size)
                            print(f"Found {total_results} products across {total_pages} pages for '{category}'.")

                    cleaned_products = clean_raw_data_coles(raw_product_list)
                    print(f"Found and cleaned {len(cleaned_products)} products on page {page_num}.")

                    timestamp = datetime.now().strftime("%Y-m-%d_%H-%M-%S")
                    file_name = f"coles_{category}_page-{page_num}_{timestamp}.json"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_products, f, indent=4)
                    print(f"Successfully saved cleaned data to {file_name}")

                except Exception as e:
                    print(f"ERROR: Failed on page {page_num} for '{category}'. Details: {e}")
                    break

                sleep_time = random.uniform(3, 7)
                print(f"Waiting for {sleep_time:.2f} seconds before next page...")
                time.sleep(sleep_time)
                
                page_num += 1
            
            print(f"--- Finished category: '{category}' ---\n")

    except Exception as e:
        print(f"\nA critical error occurred during scraping: {e}")
    
    finally:
        if driver:
            print("\n--- Scraper tool finished, closing browser. ---")
            driver.quit()
