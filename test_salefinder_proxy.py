
import requests
import json
import re

def test_sale_finder_proxy():
    """
    Fetches data from the Sale Finder service, extracts JSON from a JSONP response,
    and prints the result.
    """
    # Target URL provided in the objective
    target_url = "https://embed.salefinder.com.au/location/search/183/?sensitivity=5&noStoreSuffix=1&withStoreInfo=1"

    print(f"--- Testing Sale Finder Proxy ---")
    print(f"Fetching data from: {target_url}")

    try:
        # Make the GET request
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # The response is in JSONP format (e.g., some_function_name(...))
        jsonp_content = response.text
        print("\n--- Raw JSONP Response ---")
        print(jsonp_content)

        # Use a regular expression to extract the raw JSON data from inside the parentheses
        match = re.search(r'^\s*\w+\((.*)\);?$\s*', jsonp_content, re.DOTALL)
        if not match:
            print("\n--- ERROR ---")
            print("Could not extract JSON from the JSONP response.")
            return

        json_data_string = match.group(1)

        # Parse the extracted JSON string into a Python dictionary
        data = json.loads(json_data_string)

        print("\n--- Successfully Parsed JSON Data ---")
        # Pretty-print the JSON data
        print(json.dumps(data, indent=4))

    except requests.exceptions.RequestException as e:
        print(f"\n--- ERROR ---")
        print(f"Error fetching data from Sale Finder: {e}")
    except json.JSONDecodeError:
        print(f"\n--- ERROR ---")
        print("Failed to decode the extracted JSON string.")
    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_sale_finder_proxy()
