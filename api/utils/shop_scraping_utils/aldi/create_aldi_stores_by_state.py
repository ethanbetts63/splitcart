import json
import os
from datetime import datetime

# --- CONFIGURATION ---
SOURCE_DIR = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi'
OUTPUT_FILE = r'C:\Users\ethan\coding\splitcart\api\data\store_data\stores_aldi\aldi_stores_by_state.json'

def create_aldi_stores_by_state():
    """Reads state-specific JSON files and creates a single aggregated file."""
    print("Starting to create aldi_stores_by_state.json...")

    stores_by_state = {}
    total_stores = 0

    for filename in os.listdir(SOURCE_DIR):
        if filename.endswith('.json') and filename != 'aldi_stores_by_state.json':
            filepath = os.path.join(SOURCE_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                state_iso = data.get('metadata', {}).get('state_iso', 'unknown')
                stores = data.get('stores', [])
                
                if state_iso not in stores_by_state:
                    stores_by_state[state_iso] = []

                for store in stores:
                    stores_by_state[state_iso].append({
                        'store_name': store.get('name'),
                        'store_id': store.get('id')
                    })
                total_stores += len(stores)

    output_data = {
        "metadata": {
            "last_updated_timestamp": datetime.now().isoformat(),
            "total_stores_scraped": total_stores
        },
        "stores_by_state": stores_by_state
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print(f"Successfully created {OUTPUT_FILE} with {total_stores} stores.")

if __name__ == '__main__':
    create_aldi_stores_by_state()