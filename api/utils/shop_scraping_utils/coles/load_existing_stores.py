import json
import os

def load_existing_stores(OUTPUT_FILE):
    """Loads existing stores from the output file to avoid duplicates."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                stores_list = json.load(f)
                return {store['id']: store for store in stores_list}
        except (json.JSONDecodeError, KeyError):
            print(f"\nWarning: {OUTPUT_FILE} is corrupted or has an unexpected format. Starting fresh.")
    return {}