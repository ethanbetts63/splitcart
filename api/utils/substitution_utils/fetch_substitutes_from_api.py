
import requests
from typing import List

def fetch_substitutes_from_api(product_id: str, session: requests.Session) -> List[str]:
    """
    Retrieves a list of substitute product IDs for a given Woolworths product ID using a session.

    Args:
        product_id: The Woolworths product ID (Stockcode).
        session: The requests.Session object to use for the request.

    Returns:
        A list of substitute product IDs, or an empty list if none are found or an error occurs.
    """
    api_url = f"https://www.woolworths.com.au/api/v3/ui/subs/{product_id}"
    try:
        response = session.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        substitutes = data.get("Result", [])
        if not substitutes or not substitutes[0].get("SubstituteProductList"):
            return []

        substitute_list = substitutes[0]["SubstituteProductList"]
        return [
            sub_data.get("Product")
            for sub_data in substitute_list
            if sub_data.get("Product", {}).get("Stockcode")
        ]

    except requests.exceptions.RequestException as e:
        # We print the error in the command itself to avoid cluttering the utils
        pass # Re-raise or handle in the command
        raise e
    except ValueError:
        # Let the command handle this too
        raise ValueError("Could not decode JSON")
