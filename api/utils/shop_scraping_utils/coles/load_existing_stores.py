import json
import os

def load_existing_stores(OUTPUT_FILE):
    """Loads existing stores from the output file to avoid duplicates."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                # Load the dictionary of stores
                stores_dict = json.load(f)
                # Ensure it's a dictionary and then return it directly
                if isinstance(stores_dict, dict):
                    return stores_dict
                else:
                    print(f"\nWarning: {OUTPUT_FILE} has an unexpected format (not a dictionary). Starting fresh.")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"\nWarning: {OUTPUT_FILE} is corrupted or has an unexpected format ({e}). Starting fresh.")
    return {}
