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

def scrape_and_save_coles_data(categories_to_fetch: list, save_path: str):
    """
    Launches a browser, handles CAPTCHA, then iterates through all pages of
    the given categories, saving each page's product data to a separate file.

    Args:
        categories_to_fetch: A list of category slugs to scrape.
        save_path: The absolute path to the directory to save JSON files.
    """
    print("--- Initializing Coles Scraper Tool ---")
    driver = None

    try:
        # --- Set up and launch the visible browser ---
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
        
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

        # --- Confirm success ---
        page_title = driver.title
        if "Coles" not in page_title:
            print("\nFAILURE: Could not get to the main Coles website. Exiting scraper.")
            return
        print("SUCCESS: Security passed.\n")

        # --- Loop through each category ---
        for category in categories_to_fetch:
            print(f"--- Starting category: '{category}' ---")
            
            # --- THE FIX: Use a while loop for flexible pagination ---
            page_num = 1
            total_pages = 1 # Start with 1, will be updated after the first page scrape
            
            while page_num <= total_pages:
                print(f"Navigating to page {page_num} of {total_pages} for '{category}'...")
                browse_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
                driver.get(browse_url)
                
                try:
                    # --- Wait for the data to load and extract it ---
                    wait = WebDriverWait(driver, 10)
                    json_element = wait.until(
                        EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                    )
                    full_json_text = json_element.get_attribute('innerHTML')
                    full_data = json.loads(full_json_text)
                    
                    # --- Drill down to the product list ---
                    search_results = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {})
                    product_list = search_results.get("results", [])

                    if not product_list:
                        print(f"WARNING: Product list was empty for page {page_num} of '{category}'. Stopping this category.")
                        break # Stop processing this category if a page is empty

                    # --- If it's the first page, calculate total pages ---
                    if page_num == 1:
                        total_results = search_results.get("noOfResults", 0)
                        page_size = search_results.get("pageSize", 48)
                        if total_results > 0 and page_size > 0:
                            total_pages = math.ceil(total_results / page_size)
                            print(f"Found {total_results} products across {total_pages} pages for '{category}'.")

                    # --- Save this page's data immediately ---
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    file_name = f"coles_{category}_page-{page_num}_{timestamp}.json"
                    file_path = os.path.join(save_path, file_name)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(product_list, f, indent=4)
                    print(f"Successfully saved data for page {page_num} to {file_name}")

                except Exception as e:
                    print(f"ERROR: Failed on page {page_num} for '{category}'. Details: {e}")
                    break

                # Responsible scraping: wait between pages
                sleep_time = random.uniform(3, 7)
                print(f"Waiting for {sleep_time:.2f} seconds before next page...")
                time.sleep(sleep_time)

                # --- Increment the page counter for the while loop ---
                page_num += 1
            
            print(f"--- Finished category: '{category}' ---\n")

    except Exception as e:
        print(f"\nA critical error occurred during scraping: {e}")
    
    finally:
        if driver:
            print("\n--- Scraper tool finished, closing browser. ---")
            driver.quit()
