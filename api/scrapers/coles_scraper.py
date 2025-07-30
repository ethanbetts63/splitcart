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
    navigates to each category page, and extracts the embedded JSON data.
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
                # --- THE FINAL FIX: Use an Explicit Wait ---
                # This tells Selenium to wait up to 10 seconds for the element to appear.
                # This is the reliable way to handle race conditions.
                print("Waiting for page data to load...")
                wait = WebDriverWait(driver, 10)
                json_element = wait.until(
                    EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                )
                
                print("Page data found. Extracting JSON...")
                json_text = json_element.get_attribute('innerHTML')
                
                # Verify we got JSON before storing it
                json.loads(json_text)
                scraped_data[category] = json_text
                print(f"Successfully extracted JSON for '{category}'.")

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
