import requests
import json
import re

def get_build_id(session, category_slug):
    """
    Fetches the main category page to find the dynamic Next.js BUILD_ID.
    This ID is required to construct the correct JSON data URL.
    """
    base_url = f"https://www.coles.com.au/browse/{category_slug}"
    print(f"Fetching base page to find BUILD_ID: {base_url}")

    try:
        # The session already has cookies and headers from the warm-up call.
        response = session.get(base_url, timeout=30)
        response.raise_for_status()

        match = re.search(r'"buildId":"(.*?)"', response.text)
        if match:
            build_id = match.group(1)
            print(f"Successfully found BUILD_ID: {build_id}")
            return build_id
        else:
            print("ERROR: Could not find BUILD_ID in page source.")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Saved the received HTML to debug_page.html for inspection.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch the base page. {e}")
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
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP Error: {e.response.status_code} for URL: {api_url}.")
        print(f"Response Body: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    print("Initializing session...")
    session = requests.Session()

    session.headers.update({
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    })

    # --- NEW WARM-UP STEP ---
    # Visit the homepage first to acquire initial cookies, just like a real user would.
    # This is the same strategy used in the Woolworths script.
    print("Warming up session on homepage to acquire cookies...")
    try:
        session.get("https://www.coles.com.au/", timeout=30)
        print("Session is ready.")
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL: Failed to warm up session. Error: {e}")
        exit()
    # --- END WARM-UP STEP ---

    category_to_fetch = "fruit-vegetables"
    build_id = get_build_id(session, category_to_fetch)

    if build_id:
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
        print("\nCRITICAL: Could not proceed without a BUILD_ID.")
