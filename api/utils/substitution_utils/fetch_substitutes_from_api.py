
import requests
from typing import List

def fetch_substitutes_from_api(product_id: str) -> List[str]:
    """
    Retrieves a list of substitute product IDs for a given Woolworths product ID.

    Args:
        product_id: The Woolworths product ID (Stockcode).

    Returns:
        A list of substitute product IDs, or an empty list if none are found or an error occurs.
    """
    api_url = f"https://www.woolworths.com.au/api/v3/ui/subs/{product_id}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        substitutes = data.get("Result", [])
        if not substitutes or not substitutes[0].get("SubstituteProductList"):
            return []

        substitute_list = substitutes[0]["SubstituteProductList"]
        return [
            str(sub_data.get("Product", {}).get("Stockcode"))
            for sub_data in substitute_list
            if sub_data.get("Product", {}).get("Stockcode")
        ]

    except requests.exceptions.RequestException as e:
        print(f"API request failed for {product_id}: {e}")
        return []
    except ValueError:
        print(f"Could not decode JSON for {product_id}")
        return []
