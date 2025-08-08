
import requests
import re

def get_iga_session_id(store_id: str):
    """
    Warms up a session with IGA to get a valid sessionId.
    """
    print(f"--- Getting session ID for store: {store_id} ---")
    session = requests.Session()
    session.headers.update({
        "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    })

    # Set the store ID cookie
    session.cookies.set("iga-shop.retailerStoreId", store_id)

    # Make a request to the homepage to get the session ID
    try:
        response = session.get("https://www.igashop.com.au/", timeout=60)
        response.raise_for_status()

        # Check for the session ID in the cookies
        for cookie in session.cookies:
            if cookie.name.startswith('ab.storage.sessionId'):
                try:
                    cookie_data = json.loads(cookie.value)
                    session_id = cookie_data.get('g')
                    if session_id:
                        print(f"Found session ID in cookie '{cookie.name}': {session_id}")
                        return session_id
                except json.JSONDecodeError:
                    print(f"Could not decode cookie value: {cookie.value}")
        
        print("Could not find session ID in cookies.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return None

if __name__ == '__main__':
    # Example usage with a test store ID
    test_store_id = "48102"  # Balga IGA
    get_iga_session_id(test_store_id)
