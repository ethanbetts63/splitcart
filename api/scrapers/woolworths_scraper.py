import requests
import json


def fetch_category_data(session, category_id, page_number=1, page_size=36):
    """
    Fetches product data using a pre-warmed session that contains cookies.
    """
    api_url = "https://www.woolworths.com.au/apis/ui/browse/category"

    payload = {
        "categoryId": category_id,
        "pageNumber": page_number,
        "pageSize": page_size,
        "sortType": "PriceAsc",
        "url": f"/shop/browse/electronics?pageNumber={page_number}&sortBy=PriceAsc",
        "location": f"/shop/browse/electronics?pageNumber={page_number}&sortBy=PriceAsc&filter=SoldBy(Woolworths)",
        "formatObject": '{"name":"Electronics"}',
        "isSpecial": False,
        "isBundle": False,
        "isMobile": False,
        "filters": [{"Key": "SoldBy", "Items": [{"Term": "Woolworths"}]}],
        "token": "",
        "gpBoost": 0,
        "isHideUnavailableProducts": False,
        "isRegisteredRewardCardPromotion": False,
        "categoryVersion": "v2",
        "enableAdReRanking": False,
        "groupEdmVariants": False,
        "activePersonalizedViewType": "",
    }

    print(f"Requesting API data for Category: {category_id}, Page: {page_number}")

    try:
        # Use the provided session object to make the request
        response = session.post(api_url, json=payload, timeout=60)
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
    # --- STEP 1: Create and "Warm Up" the Session ---
    print("Initializing session...")

    # Create a single session object
    session = requests.Session()

    # Set the headers for the entire session. These will be used for all requests.
    session.headers.update(
        {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.woolworths.com.au",
            "referer": "https://www.woolworths.com.au/shop/browse/electronics",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        }
    )

    print("Warming up session to acquire cookies...")
    try:
        # Make a GET request to the homepage to get the initial cookies
        session.get("https://www.woolworths.com.au/", timeout=60)
        print("Session is ready.")
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL: Failed to warm up session and get cookies. Error: {e}")
        exit()  # Exit if we can't get cookies

    # --- STEP 2: Use the Warmed-Up Session to Fetch Data ---
    electronics_category_id = "1_B863F57"
    product_data = fetch_category_data(
        session, electronics_category_id, page_number=1, page_size=24
    )

    if product_data:
        print("\nSuccessfully retrieved API data. Preview of response:")
        print(json.dumps(product_data, indent=2))
    else:
        print("\nWARNING: Failed to retrieve API data.")
