import requests
import json
from django.conf import settings


def prefill_barcodes_from_api(product_list: list, command=None) -> list:
    """
    Enriches a list of product dictionaries with barcodes by calling a dedicated API endpoint.
    """
    if command:
        command.stdout.write(f"  - Prefilling barcodes via API for {len(product_list)} products...")

    # Step 1: Identify products that need a barcode lookup.
    names_to_lookup = set()
    products_to_update = []
    for product_data in product_list:
        if not product_data.get('barcode'):
            incoming_normalized_string = product_data.get('normalized_name_brand_size')
            if not incoming_normalized_string:
                continue
            
            # Find the canonical name using the translation table.
            canonical_name = incoming_normalized_string
            names_to_lookup.add(canonical_name)
            products_to_update.append(product_data)

    if not names_to_lookup:
        if command:
            command.stdout.write("  - No products required barcode prefilling.")
        return product_list

    # Step 2: Call the API to get barcodes for the collected names.
    server_url = settings.API_SERVER_URL
    api_key = settings.INTERNAL_API_KEY
    if not server_url or not api_key:
        if command:
            command.stdout.write(command.style.ERROR("API_SERVER_URL or INTERNAL_API_KEY not configured. Skipping barcode prefill."))
        return product_list

    url = f"{server_url.rstrip('/')}/api/products/barcodes/"
    headers = {
        'Content-Type': 'application/json',
        'X-Internal-API-Key': api_key,
    }
    payload = {"names": list(names_to_lookup)}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        barcode_map = response.json()
    except requests.exceptions.RequestException as e:
        if command:
            command.stdout.write(command.style.ERROR(f"  - API call for barcodes failed: {e}"))
        return product_list # Return original list on failure

    # Step 3: Update the product list with the barcodes received from the API.
    prefilled_count = 0
    for product_data in products_to_update:
        incoming_normalized_string = product_data.get('normalized_name_brand_size')
        canonical_name = incoming_normalized_string
        
        if canonical_name in barcode_map:
            product_data['barcode'] = barcode_map[canonical_name]
            prefilled_count += 1

    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Prefilled {prefilled_count} barcodes from API."))

    return product_list