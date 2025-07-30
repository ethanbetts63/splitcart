import json
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def fetch_coles_data(categories_to_fetch: list) -> dict:
    """
    Launches a visible Selenium browser, pauses for manual CAPTCHA solving,
    fetches data for a given list of categories, and returns the raw JSON.

    Args:
        categories_to_fetch: A list of category slugs (e.g., ['fruit-vegetables']).

    Returns:
        A dictionary where keys are category slugs and values are the raw
        JSON strings of the data fetched. Returns an empty dict on failure.
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

        # --- Confirm success and get Build ID ---
        page_title = driver.title
        if "Coles" not in page_title:
            print("\nFAILURE: Could not get to the main Coles website. Exiting scraper.")
            return {}

        print("SUCCESS: Security passed. Finding Build ID...")
        page_source = driver.page_source
        match = re.search(r'"buildId":"([^"]+)"', page_source)
        
        if not match:
            print("CRITICAL: Could not find Build ID. Exiting scraper.")
            return {}

        build_id = match.group(1)
        print(f"Successfully got Build ID: {build_id}\n")

        # --- Loop through categories and fetch data ---
        for category in categories_to_fetch:
            print(f"Fetching data for category: '{category}'...")
            api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category}.json?page=1"
            
            driver.get(api_url)
            
            json_text = driver.find_element(webdriver.common.by.By.TAG_NAME, "body").text
            
            # Verify we got JSON before storing it
            try:
                json.loads(json_text)
                scraped_data[category] = json_text
                print(f"Successfully captured JSON for '{category}'.")
            except json.JSONDecodeError:
                print(f"ERROR: Failed to get valid JSON for '{category}'. The content was not JSON.")

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
