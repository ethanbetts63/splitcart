
import json
import os
from typing import Dict, Any
from django.conf import settings

DISCOVERED_PRODUCTS_FILE = os.path.join(settings.BASE_DIR, 'api', 'data', 'discovered_substitutes.json')

def save_discovered_product(product_data: Dict[str, Any]):
    """
    Saves a newly discovered product's data to a JSON file if it's not already present.

    Args:
        product_data: A dictionary containing the product details from the API.
    """
    product_id = product_data.get('Stockcode')
    if not product_id:
        return # Cannot save a product without an ID

    # Ensure the directory exists
    os.makedirs(os.path.dirname(DISCOVERED_PRODUCTS_FILE), exist_ok=True)

    # Load existing products
    try:
        with open(DISCOVERED_PRODUCTS_FILE, 'r') as f:
            discovered_products = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        discovered_products = []

    # Check if product is already in the file
    if any(p.get('Stockcode') == product_id for p in discovered_products):
        return # Product already discovered

    # Add the new product and save
    discovered_products.append(product_data)
    with open(DISCOVERED_PRODUCTS_FILE, 'w') as f:
        json.dump(discovered_products, f, indent=4)
