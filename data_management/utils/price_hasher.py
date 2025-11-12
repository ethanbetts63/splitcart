
import json
import hashlib
from decimal import Decimal

def generate_price_hash(product_data: dict) -> str:
    """
    Generates a deterministic MD5 hash from the core fields of a price record.
    This hash represents the fingerprint of the price data itself, independent
    of the product, store, or scrape date.

    Args:
        product_data: A dictionary containing the product's price-related fields.

    Returns:
        A string containing the MD5 hexdigest of the price data.
    """
    # These are the fields that define the unique state of a price's details.
    hash_keys = [
        'price_current',
        'price_was',
        'unit_price',
        'unit_of_measure',
        'per_unit_price_string',
        'is_on_special',
    ]

    # Create a dictionary with only the relevant keys for hashing
    hash_data = {key: product_data.get(key) for key in hash_keys}

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
