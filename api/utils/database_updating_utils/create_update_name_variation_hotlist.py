import json
import os

HOTLIST_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'name_variation_hotlist.json')

def read_hotlist():
    """Reads the hotlist file, creating it if it doesn't exist."""
    if not os.path.exists(HOTLIST_PATH):
        with open(HOTLIST_PATH, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(HOTLIST_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is empty or corrupt, treat it as an empty list
        return []

def add_to_hotlist(new_variation):
    """Adds a new variation to the hotlist."""
    hotlist = read_hotlist()
    hotlist.append(new_variation)
    with open(HOTLIST_PATH, 'w') as f:
        json.dump(hotlist, f, indent=4)

def clear_hotlist():
    """Clears all entries from the hotlist."""
    with open(HOTLIST_PATH, 'w') as f:
        json.dump([], f)

def bulk_add_to_hotlist(new_entries: list):
    """
    Adds a list of new variations to the hotlist in a single batch operation.
    """
    if not new_entries:
        return
        
    hotlist = read_hotlist()
    hotlist.extend(new_entries)
    with open(HOTLIST_PATH, 'w') as f:
        json.dump(hotlist, f, indent=4)
