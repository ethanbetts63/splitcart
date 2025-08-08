import json

def save_stores_incrementally(OUTPUT_FILE, stores_dict):
    """Saves the dictionary of cleaned stores to the output file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stores_dict, f, indent=4)
