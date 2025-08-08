import json
import os
import re
from datetime import date

# --- CONFIGURATION ---
SOURCE_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths\woolworths_stores_raw.json'
BASE_OUTPUT_DIR = 'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_woolworths'

def slugify(text):
    """Converts a string into a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove non-alphanumeric characters
    text = re.sub(r'[\s_]+', '-', text)   # Replace spaces/underscores with hyphens
    return text

def organize_woolworths_stores():
    """Reads the raw stores file and organizes stores into brand/state specific files with metadata."""
    print(f"Starting organization of {SOURCE_FILE}...")

    # 1. Read the source file
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            all_stores_dict = json.load(f)
            all_stores_list = list(all_stores_dict.values())
    except FileNotFoundError:
        print(f"Error: Source file not found at {SOURCE_FILE}. Nothing to do.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {SOURCE_FILE}.")
        return

    # 2. Group stores by brand and then by state
    grouped_stores = {}
    for store in all_stores_list:
        try:
            brand_name = store.get('Division', 'unknown-brand')
            state = store.get('State', 'unknown-state').lower()

            brand_slug = slugify(brand_name)

            if brand_slug not in grouped_stores:
                grouped_stores[brand_slug] = {}
            if state not in grouped_stores[brand_slug]:
                grouped_stores[brand_slug][state] = []
            
            grouped_stores[brand_slug][state].append(store)

        except Exception as e:
            print(f"Skipping store due to error: {e}\nProblematic store data: {store}")

    # 3. Write the grouped data to respective files with metadata
    if not os.path.exists(BASE_OUTPUT_DIR):
        print(f"Base output directory does not exist: {BASE_OUTPUT_DIR}")
        return

    today_date = date.today().isoformat()

    for brand_slug, states in grouped_stores.items():
        brand_dir = os.path.join(BASE_OUTPUT_DIR, brand_slug)
        os.makedirs(brand_dir, exist_ok=True)
        
        for state, stores in states.items():
            output_filename = os.path.join(brand_dir, f"{state}.json")
            
            # Create the final data structure with metadata
            output_data = {
                "metadata": {
                    "number_of_stores": len(stores),
                    "company": "woolworths",
                    "brand": brand_slug,
                    "state": state.upper(),
                    "date_scraped": today_date
                },
                "stores": stores
            }

            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4)
                print(f"Wrote {len(stores)} stores to {output_filename}")
            except IOError as e:
                print(f"Error writing to file {output_filename}: {e}")

    # 4. Delete the original source file after successful processing
    try:
        os.remove(SOURCE_FILE)
        print(f"Successfully removed original file: {SOURCE_FILE}")
    except OSError as e:
        print(f"Error deleting source file: {e}")

    print("\nOrganization complete.")