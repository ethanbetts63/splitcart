import requests
import json
import time
import random
from coles_scraper import get_coles_session_details

def fetch_category_data(session, build_id, category_slug, page=1):
    """
    Uses a cookie-filled session to fetch product data for a specific category.
    """
    api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category_slug}.json?page={page}"
    
    print(f"--- Requesting data for category: '{category_slug}' ---")
    
    try:
        response = session.get(api_url, timeout=20)
        response.raise_for_status()
        # It's crucial to check if the response is actually JSON before parsing
        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        else:
            print("ERROR: Response was not in JSON format. The server may have blocked the request.")
            print("Response text:", response.text[:200]) # Print first 200 chars of the response
            return None
            
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP Error: {e.response.status_code} for URL: {api_url}.")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        
    return None


if __name__ == "__main__":
    print("STEP 1: Launching browser to get session details from Coles...")
    build_id, browser_cookies = get_coles_session_details()

    if not build_id or not browser_cookies:
        print("\nCRITICAL: Could not get buildId or cookies. Exiting.")
        exit()

    print(f"\nSuccessfully got Build ID: {build_id}")
    print("Successfully got session cookies.")
    
    # --- The Hand-off ---
    api_session = requests.Session()

    # --- THE FIX: Set browser-like headers for the session ---
    # This makes the requests session look identical to the browser that passed the security check.
    api_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.coles.com.au/",
        "Connection": "keep-alive",
    })

    # Load the cookies from the browser into the requests session.
    for cookie in browser_cookies:
        api_session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
    
    print("\nSTEP 2: Headers and cookies loaded into API session. Ready to fetch data.")
    
    categories_to_fetch = [
        "fruit-vegetables",
        "meat-seafood"
    ]

    for category in categories_to_fetch:
        product_data = fetch_category_data(api_session, build_id, category)

        if product_data:
            results = product_data.get("pageProps", {}).get("searchResults", {})
            products = results.get("results", [])
            total_products = results.get("noOfResults", 0)

            print(f"Found {len(products)} products on page 1 of {total_products} total for this category.")
            
            if products:
                first_product = products[0].get('_source', {})
                name = first_product.get('name')
                price = first_product.get('pricing', {}).get('now')
                print(f"Sample Product: {name} - ${price}")
        
        if category != categories_to_fetch[-1]:
            sleep_time = random.uniform(3, 7)
            print(f"\nWaiting for {sleep_time:.2f} seconds before next category...")
            time.sleep(sleep_time)

    print("\n--- Scraping complete ---")
