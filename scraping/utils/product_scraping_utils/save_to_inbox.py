import os
import json
import uuid
from django.conf import settings

def save_to_inbox(product_data: dict, metadata: dict):
    """
    Saves a single product's data to a JSON file in the product_inbox directory.
    """
    inbox_path = os.path.join(settings.BASE_DIR, 'scraping', 'data', 'product_inbox')
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path)

    # Combine product data with scrape metadata for context
    full_data = {
        'metadata': metadata,
        'product': product_data
    }

    # Generate a unique filename
    filename = f"{metadata.get('company', 'unknown')}_{product_data.get('sku', 'no_id')}_{uuid.uuid4()}.json"
    file_path = os.path.join(inbox_path, filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving to inbox: {e}")
        return False
