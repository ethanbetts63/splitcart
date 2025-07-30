import requests
import json
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_build_id_with_enhanced_selenium(category_slug):
    """
    Enhanced Selenium setup with better anti-detection measures
    """
    base_url = f"https://www.coles.com.au/browse/{category_slug}"
    print(f"Initializing enhanced stealth browser to visit: {base_url}")

    chrome_options = Options()
    
    # Comment out headless for debugging - Incapsula often blocks headless browsers
    # chrome_options.add_argument("--headless")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # More realistic browser profile
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")  # Faster loading
    chrome_options.add_argument("--disable-javascript")  # Try without JS first
    
    # Randomize window size
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    chrome_options.add_argument(f"--window-size={width},{height}")
    
    # Use a more recent user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute script to hide webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        # Add random delay before visiting
        time.sleep(random.uniform(2, 5))
        
        driver.get(base_url)
        
        # Wait longer and check for specific elements
        print("Waiting for page to load and pass security checks...")
        
        # Wait up to 30 seconds for the page to load properly
        wait = WebDriverWait(driver, 30)
        
        # Try to wait for a specific element that indicates the page loaded
        try:
            # Look for any script tag with buildManifest or similar
            wait.until(lambda d: "buildManifest" in d.page_source or "pageProps" in d.page_source)
        except:
            print("Timeout waiting for page elements, proceeding anyway...")
        
        # Additional wait
        time.sleep(random.uniform(5, 10))
        
        page_source = driver.page_source
        print("Successfully retrieved page source from the browser.")
        
        # Check if we got the Incapsula challenge page
        if "Incapsula" in page_source or "_Incapsula_Resource" in page_source:
            print("WARNING: Detected Incapsula challenge page. Bot detection is active.")
            # Save for debugging
            with open("incapsula_challenge.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            return None
        
        # Look for build ID in multiple possible locations
        patterns = [
            r'/_next/static/([^/]+)/_buildManifest\.js',
            r'"buildId":"([^"]+)"',
            r'buildId:\"([^\"]+)\"',
            r'BUILD_ID["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_source)
            if match:
                build_id = match.group(1)
                print(f"Successfully found BUILD_ID: {build_id}")
                return build_id
        
        print("ERROR: Could not find BUILD_ID in any expected location.")
        # Save the page for debugging
        with open("debug_selenium_page_enhanced.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Saved page source for debugging.")
        return None

    except Exception as e:
        print(f"ERROR: Exception occurred: {e}")
        return None
    finally:
        driver.quit()


def try_direct_api_approach(category_slug):
    """
    Try to find the build ID by examining the network requests or trying common patterns
    """
    print("Attempting direct API approach...")
    
    # Sometimes build IDs follow patterns, let's try some common ones
    # You can find these by inspecting successful requests in browser dev tools
    common_build_patterns = [
        "development",
        "static",
        "production",
        "_next",
        # Add more if you find patterns
    ]
    
    session = requests.Session()
    session.headers.update({
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': f'https://www.coles.com.au/browse/{category_slug}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    })
    
    # First, try to get cookies by visiting the main page
    try:
        print("Getting cookies from main page...")
        session.get("https://www.coles.com.au/", timeout=10)
        time.sleep(2)  # Brief pause
        session.get(f"https://www.coles.com.au/browse/{category_slug}", timeout=10)  
        time.sleep(2)  # Brief pause
    except Exception as e:
        print(f"Warning: Could not get cookies: {e}")
    
    for build_id in common_build_patterns:
        try:
            test_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category_slug}.json"
            print(f"Testing build ID: {build_id}")
            response = session.get(test_url, timeout=10)
            print(f"Response status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                # Check if it's actually JSON and not an error page
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type and response.text.strip():
                    try:
                        # Try to parse to make sure it's valid JSON
                        data = response.json()
                        print(f"Found working build ID: {build_id}")
                        return build_id
                    except json.JSONDecodeError:
                        print(f"Build ID {build_id} returned 200 but invalid JSON")
                        continue
        except Exception as e:
            print(f"Error testing {build_id}: {e}")
            continue
    
    return None


def fetch_coles_category_data(session, build_id, category_slug, page_number=1):
    """
    Fetches product data for a specific category page from Coles' Next.js data URL.
    """
    api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category_slug}.json?page={page_number}"
    print(f"Requesting API data from: {api_url}")

    try:
        response = session.get(api_url, timeout=30)
        response.raise_for_status()

        print(f"Successfully fetched API data. Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Response length: {len(response.text)} characters")
        
        # Debug: Print first 200 characters of response
        print(f"Response preview: {response.text[:200]}...")
        
        # Check if response is actually JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            print(f"WARNING: Expected JSON but got content-type: {content_type}")
            print(f"Full response: {response.text}")
            return None
        
        # Try to parse JSON with better error handling
        if response.text.strip():
            return response.json()
        else:
            print("ERROR: Empty response body")
            return None

    except json.JSONDecodeError as e:
        print(f"ERROR: JSON Decode Error: {e}")
        print(f"Response text: {response.text}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP Error: {e.response.status_code} for URL: {api_url}.")
        print(f"Response Body: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    category_to_fetch = "fruit-vegetables"
    
    # Try multiple approaches
    build_id = None
    
    # Approach 1: Try direct API patterns first (faster)
    print("=== APPROACH 1: Direct API Pattern Testing ===")
    build_id = try_direct_api_approach(category_to_fetch)
    
    # Approach 2: Enhanced Selenium if direct approach fails
    if not build_id:
        print("\n=== APPROACH 2: Enhanced Selenium ===")
        build_id = get_build_id_with_enhanced_selenium(category_to_fetch)
    
    # If we have a build_id, try to fetch data
    if build_id:
        print(f"\n=== FETCHING DATA WITH BUILD_ID: {build_id} ===")
        session = requests.Session()
        session.headers.update({
            'accept': 'application/json',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': f'https://www.coles.com.au/browse/{category_to_fetch}',
        })

        product_data = fetch_coles_category_data(
            session, build_id, category_to_fetch, page_number=1
        )

        if product_data:
            print("\nSuccessfully retrieved API data. Preview of response:")
            products = product_data.get("pageProps", {}).get("searchResults", {}).get("results", [])
            print(f"Found {len(products)} products on this page.")
            if products:
                print(json.dumps(products[0], indent=2))
        else:
            print("\nWARNING: Failed to retrieve API data.")
    else:
        print("\nCRITICAL: Could not obtain BUILD_ID with any method.")
        print("\nSUGGESTIONS:")
        print("1. Try running with visible browser (comment out headless mode)")
        print("2. Check if you need to solve CAPTCHA manually")
        print("3. Consider using residential proxies")
        print("4. Try accessing from a different IP/location")