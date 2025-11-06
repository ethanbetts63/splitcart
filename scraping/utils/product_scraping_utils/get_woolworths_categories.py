import requests

def get_woolworths_categories(command, dev: bool = False):
    """
    Fetches the category hierarchy from Woolworths' api and extracts a flattened list of categories.
    """
    if dev:
        api_url = "http://127.0.0.1:8000/static/woolworths_categories.json"
    else:
        api_url = "https://www.woolworths.com.au/apis/ui/PiesCategoriesWithSpecials"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://www.woolworths.com.au",
        "referer": "https://www.woolworths.com.au/shop/browse/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        command.stdout.write(f"ERROR: Request failed when fetching categories: {e}\n")
        return []
    except ValueError: # Catches JSON decoding errors
        command.stdout.write("ERROR: Failed to decode JSON when fetching categories.\n")
        return []

    categories = []
    # The actual categories are not under 'Specials' but are siblings
    for category in data.get('Categories', [])[1:]:
        for child in category.get('Children', []):
            categories.append((child.get('UrlFriendlyName'), child.get('NodeId')))

    return categories