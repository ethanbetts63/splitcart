import undetected_chromedriver as uc
import requests
import json
import re
import time
import random

def get_build_id_undetected(category_slug):
    """
    Uses undetected-chromedriver which is specifically designed to bypass bot detection
    """
    base_url = f"https://www.coles.com.au/browse/{category_slug}"
    print(f"Using undetected Chrome driver to visit: {base_url}")
    
    options = uc.ChromeOptions()
    
    # Keep it visible for debugging - many bot detections fail with headless
    # options.add_argument("--headless")
    
    # Basic options
    options.add_argument("--no-first-run")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        # Create undetected Chrome instance
        driver = uc.Chrome(options=options)
        
        # Random delay
        time.sleep(random.uniform(3, 7))
        
        # Navigate to page
        driver.get(base_url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(15)  # Give it more time
        
        # Check if we passed the challenge
        page_source = driver.page_source
        
        if "Incapsula" in page_source or "_Incapsula_Resource" in page_source:
            print("Still getting Incapsula challenge. Manual intervention may be required.")
            input("Please solve any challenges in the browser, then press Enter to continue...")
            time.sleep(5)
            page_source = driver.page_source
        
        # Look for build ID
        patterns = [
            r'/_next/static/([^/]+)/_buildManifest\.js',
            r'"buildId":"([^"]+)"',
            r'buildId:\"([^\"]+)\"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_source)
            if match:
                build_id = match.group(1)
                print(f"Found BUILD_ID: {build_id}")
                return build_id
        
        print("Could not find BUILD_ID")
        with open("undetected_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    category_to_fetch = "fruit-vegetables"
    build_id = get_build_id_undetected(category_to_fetch)
    
    if build_id:
        print(f"Success! Build ID: {build_id}")
        # Continue with your existing fetch_coles_category_data function
    else:
        print("Failed to get build ID")