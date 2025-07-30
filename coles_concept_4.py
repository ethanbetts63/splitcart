import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
#this works.
def main():
    """
    Launches a Selenium browser and navigates to the Coles homepage.
    The goal is to see if we can get past the initial bot-check page.
    """
    print("--- Starting Selenium Test ---")

    driver = None  # Initialize driver to None
    try:
        print("[STEP 1] Setting up Chrome options...")
        options = webdriver.ChromeOptions()
        # Running in headless mode can sometimes be detected. For this test, we run with a visible browser.
        # options.add_argument('--headless') 
        options.add_argument('--start-maximized')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36')


        print("[STEP 2] Initializing Chrome WebDriver...")
        # webdriver-manager will automatically download the correct driver for your version of Chrome
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        url = "https://www.coles.com.au"
        print(f"[STEP 3] Navigating to {url}...")
        driver.get(url)

        # Let's wait for a moment to see what page loads. 
        # The Incapsula check might take a few seconds.
        print("[STEP 4] Waiting for 10 seconds to observe the page...")
        time.sleep(10)

        # Check the title of the page to see if we landed on the correct site
        page_title = driver.title
        print(f"[STEP 5] Page title is: '{page_title}'")

        if "Coles" in page_title:
            print("\nSUCCESS: The page title contains 'Coles'. It looks like we got to the main website!")
        else:
            print("\nFAILURE: The page title does not contain 'Coles'. We may still be on a block page.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    
    finally:
        if driver:
            print("\n[STEP 6] Closing the browser.")
            driver.quit()
        
        print("\n--- Selenium Test Finished ---")


if __name__ == "__main__":
    main()

