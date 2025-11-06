
import json
import hashlib
from decimal import Decimal

def generate_price_hash(product_data: dict, store_id: str) -> str:
    """
    Generates a deterministic MD5 hash from the core fields of a price record.

    Args:
        product_data: A dictionary containing the product's price-related fields.
        store_id: The ID of the store for which the price is being recorded.

    Returns:
        A string containing the MD5 hexdigest of the price data.
    """
    # These are the fields that define the unique state of a price
    hash_keys = [
        'price_current',
        'price_was',
        'unit_price',
        'unit_of_measure',
        'per_unit_price_string',
        'is_on_special',
        'scraped_date',
        'normalized_name_brand_size'  # Proxy for product FK
    ]

    # Create a dictionary with only the relevant keys for hashing
    hash_data = {key: product_data.get(key) for key in hash_keys}
    
    # Add the store_id, which is a crucial part of the price's identity
    hash_data['store_id'] = store_id

    # Convert Decimal types to strings to ensure JSON serializability
    for key, value in hash_data.items():
        if isinstance(value, Decimal):
            hash_data[key] = str(value)

    # Create a canonical string representation by dumping to JSON with sorted keys.
    # This ensures that the hash is the same regardless of dictionary key order.
    canonical_string = json.dumps(hash_data, sort_keys=True)

    # Encode the string to bytes and generate the MD5 hash
    hash_object = hashlib.md5(canonical_string.encode('utf-8'))
    
    return hash_object.hexdigest()
