import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_coles_data(categories_to_fetch: list) -> dict:
    """
    Launches a visible Selenium browser, pauses for manual CAPTCHA solving,
    navigates to each category page, and extracts only the product list JSON.

    Args:
        categories_to_fetch: A list of category slugs (e.g., ['fruit-vegetables']).

    Returns:
        A dictionary where keys are category slugs and values are the raw
        JSON strings of just the product list. Returns an empty dict on failure.
    """
    print("--- Initializing Coles Scraper Tool ---")
    driver = None
    scraped_data = {}

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
            return {}
        print("SUCCESS: Security passed.\n")

        # --- Loop through categories and fetch data from the page source ---
        for category in categories_to_fetch:
            print(f"Navigating to category page: '{category}'...")
            browse_url = f"https://www.coles.com.au/browse/{category}"
            
            driver.get(browse_url)
            
            try:
                # --- Wait for the page data to load ---
                print("Waiting for page data to load...")
                wait = WebDriverWait(driver, 10)
                json_element = wait.until(
                    EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                )
                
                print("Page data found. Extracting and trimming JSON...")
                full_json_text = json_element.get_attribute('innerHTML')
                full_data = json.loads(full_json_text)
                
                # --- THE FIX: Drill down to the product list ---
                # This follows the path: props -> pageProps -> searchResults -> results
                product_list = full_data.get("props", {}).get("pageProps", {}).get("searchResults", {}).get("results", [])

                if not product_list:
                    print(f"WARNING: Found page data, but the product list was empty for '{category}'.")
                    continue

                # Convert just the product list back to a nicely formatted JSON string
                product_json_string = json.dumps(product_list, indent=4)
                
                scraped_data[category] = product_json_string
                print(f"Successfully extracted JSON for {len(product_list)} products in '{category}'.")

            except Exception as e:
                print(f"ERROR: Could not find or process '__NEXT_DATA__' for '{category}'. Details: {e}")

            # Responsible scraping: wait between requests
            if category != categories_to_fetch[-1]:
                sleep_time = random.uniform(3, 6)
                print(f"Waiting for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

    except Exception as e:
        print(f"\nAn error occurred during scraping: {e}")
    
    finally:
        if driver:
            print("\n--- Scraper tool finished, closing browser. ---")
            driver.quit()
        
    return scraped_data
