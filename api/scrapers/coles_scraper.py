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
    and then uses background JavaScript requests to fetch data for a given
    list of categories, returning the raw JSON.

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
        # Set a timeout for asynchronous scripts
        driver.set_script_timeout(30)

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

        # --- Loop through categories and fetch data using JavaScript ---
        for category in categories_to_fetch:
            print(f"Fetching data for category: '{category}'...")
            api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category}.json?page=1"
            
            # This JavaScript uses the browser's fetch API to get data in the background
            # It's asynchronous, so Selenium waits for the callback to be called.
            js_script = """
                const url = arguments[0];
                const callback = arguments[arguments.length - 1];
                fetch(url)
                    .then(response => response.text())
                    .then(text => callback(text))
                    .catch(error => callback(JSON.stringify({_error: error.toString()})));
            """
            
            # Execute the async script and get the result
            json_text = driver.execute_async_script(js_script, api_url)
            
            # Verify we got JSON before storing it
            try:
                # Check for a custom error object from our JS catch block
                test_json = json.loads(json_text)
                if isinstance(test_json, dict) and '_error' in test_json:
                     print(f"ERROR: JavaScript fetch failed for '{category}'. Details: {test_json['_error']}")
                     continue

                scraped_data[category] = json_text
                print(f"Successfully captured JSON for '{category}'.")
            except (json.JSONDecodeError, TypeError):
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
