import requests
import json
import os

# --- CONFIGURATION ---
# The servicePoint can be any valid store ID. Using G452 as found in the example.
ALDI_CATEGORIES_URL = "https://api.aldi.com.au/v2/product-category-tree?serviceType=walk-in&servicePoint=G452"
OUTPUT_DIR = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'aldi_categories.json')

def get_aldi_categories():
    """
    Fetches the category hierarchy from the ALDI API, extracts all categories
    (including children), and saves them to a file.
    Returns a list of (category_slug, category_key) tuples.
    """
    print("Fetching ALDI categories...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    try:
        # First, check if the file exists and is recent.
        # For this implementation, we will always fetch for simplicity.
        
        response = requests.get(ALDI_CATEGORIES_URL)
        response.raise_for_status()
        data = response.json()

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        print(f"Successfully saved raw ALDI categories to {OUTPUT_FILE}")

        # Now, let's process this to get the list we need for the scraper
        all_categories = []
        
        def extract_categories(categories):
            for category in categories:
                # Add the parent category
                all_categories.append((category.get('urlSlugText'), category.get('key')))
                # Recursively add children
                if category.get('children'):
                    extract_categories(category.get('children'))

        extract_categories(data.get('data', []))
        
        print(f"Extracted {len(all_categories)} categories and sub-categories.")
        return all_categories

    except requests.exceptions.RequestException as e:
        print(f"Error fetching categories: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON from category API.")
        return None

if __name__ == '__main__':
    get_aldi_categories()
