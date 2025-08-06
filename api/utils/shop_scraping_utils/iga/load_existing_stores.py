import json
import os

def load_existing_stores(STORES_FILE):
    """Loads existing stores from the output file to avoid duplicates."""
    if os.path.exists(STORES_FILE):
        try:
            with open(STORES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: {STORES_FILE} is corrupted or has an unexpected format. Starting fresh.")
    return []