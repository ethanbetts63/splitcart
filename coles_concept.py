import requests
import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def get_build_id_with_selenium(category_slug):
    """
    Uses a real browser via Selenium to bypass bot detection (like Incapsula)
    and get the page source after JavaScript has rendered.
    """
    base_url = f"https://www.coles.com.au/browse/{category_slug}"
    print(f"Initializing browser to visit: {base_url}")

    # --- Selenium Setup ---
    # Set Chrome options. 'headless' runs Chrome without a visible browser window.
    # You can comment out the next two lines to watch the browser work.
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    
    # Automatically downloads and manages the correct driver for your version of Chrome.
    service = ChromeService(ChromeDriverManager().install())
    
    # Initialize the browser driver.
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to the page.
        driver.get(base_url)

        # --- CRITICAL STEP ---
        # Wait for the page to load completely. This gives Incapsula's
        # JavaScript challenge time to run and for the real page to be loaded.
        # This value may need to be adjusted if your connection is slow.
        print("Waiting for page to load and pass security checks...")
        time.sleep(10) # Wait for 10 seconds

        # Get the page source *after* the browser has rendered it.
        page_source = driver.page_source
        print("Successfully retrieved page source from the browser.")

        # --- Find the Build ID ---
        # We search for the build ID in a script tag, a reliable location.
        match = re.search(r'/_next/static/([^/]+)/_buildManifest.js', page_source)
        
        if match:
            build_id = match.group(1)
            print(f"Successfully found BUILD_ID: {build_id}")
            return build_id
        else:
            # If it fails, save the browser's HTML for debugging.
            print("ERROR: Could not find BUILD_ID in the browser's page source.")
            with open("debug_selenium_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("Saved the browser's HTML to debug_selenium_page.html for inspection.")
            return None

    finally:
        # Always close the browser window to free up resources.
        print("Closing browser.")
        driver.quit()


def fetch_coles_category_data(session, build_id, category_slug, page_number=1):
    """
    Fetches product data for a specific category page from Coles' Next.js data URL.
    (This function remains unchanged as it's just an API call).
    """
    api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category_slug}.json?page={page_number}"
    print(f"Requesting API data from: {api_url}")

    try:
        response = session.get(api_url, timeout=30)
        response.raise_for_status()

        print(f"Successfully fetched API data. Status Code: {response.status_code}")
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP Error: {e.response.status_code} for URL: {api_url}.")
        print(f"Response Body: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    category_to_fetch = "fruit-vegetables"
    
    # --- Step 1: Use Selenium to get the Build ID ---
    build_id = get_build_id_with_selenium(category_to_fetch)

    # --- Step 2: Use the faster 'requests' library for the API call ---
    if build_id:
        # We still use a requests session for the actual API call as it's more efficient.
        session = requests.Session()
        session.headers.update({
            'accept': 'application/json', # We expect JSON data from the API
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        })

        product_data = fetch_coles_category_data(
            session, build_id, category_to_fetch, page_number=1
        )

        if product_data:
            print("\nSuccessfully retrieved API data. Preview of response:")
            # The data structure for products in the API response
            products = product_data.get("pageProps", {}).get("searchResults", {}).get("results", [])
            print(f"Found {len(products)} products on this page.")
            if products:
                # Print the first product as a sample
                print(json.dumps(products[0], indent=2))
        else:
            print("\nWARNING: Failed to retrieve API data.")
    else:
        print("\nCRITICAL: Could not proceed without a BUILD_ID.")

