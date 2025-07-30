import json
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def run_coles_scraper():
    """
    Launches a visible Selenium browser, gets past security, and then uses
    the same browser session to fetch data from the Coles API.
    """
    print("--- Starting Coles Scraper ---")
    driver = None  # Initialize driver to None

    try:
        # --- STEP 1: Set up and launch the visible browser ---
        print("Initializing Chrome WebDriver...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # --- STEP 2: Navigate and pass security check ---
        url = "https://www.coles.com.au"
        print(f"Navigating to {url}...")
        driver.get(url)

        print("Waiting for 10 seconds to ensure page loads and passes security...")
        time.sleep(10)

        # --- STEP 3: Confirm success and get Build ID ---
        page_title = driver.title
        print(f"Landed on page with title: '{page_title}'")

        if "Coles" not in page_title:
            print("\nFAILURE: Could not get to the main Coles website. Exiting.")
            return

        print("\nSUCCESS: Security passed. Now finding Build ID...")
        page_source = driver.page_source
        match = re.search(r'"buildId":"([^"]+)"', page_source)
        
        if not match:
            print("CRITICAL: Found 'Coles' in title, but could not find Build ID. Exiting.")
            return

        build_id = match.group(1)
        print(f"Successfully got Build ID: {build_id}\n")

        # --- STEP 4: Loop through categories and fetch data ---
        categories_to_fetch = [
            "fruit-vegetables",
            "meat-seafood",
            "bakery"
        ]

        for category in categories_to_fetch:
            print(f"--- Requesting data for category: '{category}' ---")
            api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category}.json?page=1"
            
            # Use the already open, authenticated browser to go to the API URL
            driver.get(api_url)
            
            # The JSON data is inside a <pre> tag. Find it and get its text.
            pre_tag_content = driver.find_element(webdriver.common.by.By.TAG_NAME, "pre").text
            product_data = json.loads(pre_tag_content)

            if product_data:
                results = product_data.get("pageProps", {}).get("searchResults", {})
                products = results.get("results", [])
                total_products = results.get("noOfResults", 0)

                print(f"Found {len(products)} products on page 1 of {total_products} total.")
                
                if products:
                    first_product = products[0].get('_source', {})
                    name = first_product.get('name')
                    price = first_product.get('pricing', {}).get('now')
                    print(f"Sample Product: {name} - ${price}")

            # Responsible scraping: wait between requests
            if category != categories_to_fetch[-1]:
                sleep_time = random.uniform(4, 8)
                print(f"\nWaiting for {sleep_time:.2f} seconds before next category...")
                time.sleep(sleep_time)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    
    finally:
        if driver:
            print("\n--- Scraping complete, closing browser. ---")
            driver.quit()
        else:
            print("\n--- Scraper finished ---")


if __name__ == "__main__":
    run_coles_scraper()
