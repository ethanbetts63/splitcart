import requests
import json
from django.conf import settings


def prefill_barcodes_from_api(product_list: list, command=None, dev: bool = False) -> list:
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
    server_url = "http://127.0.0.1:8000" if dev else settings.API_SERVER_URL
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

    if command:
        command.stdout.write(f"  - Querying API with {len(names_to_lookup)} unique product names.")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        api_response_map = response.json()
        if command:
            command.stdout.write(f"  - API returned data for {len(api_response_map)} products.")
    except requests.exceptions.RequestException as e:
        if command:
            command.stdout.write(command.style.ERROR(f"  - API call for barcodes failed: {e}"))
        return product_list # Return original list on failure

    # Step 3: Update the product list with the data received from the API.
    prefilled_count = 0
    for product_data in products_to_update:
        incoming_normalized_string = product_data.get('normalized_name_brand_size')
        canonical_name = incoming_normalized_string
        
        if canonical_name in api_response_map:
            product_api_data = api_response_map[canonical_name]
            if product_api_data.get('barcode'):
                product_data['barcode'] = product_api_data['barcode']
                prefilled_count += 1
            if product_api_data.get('has_no_coles_barcode'):
                product_data['has_no_coles_barcode'] = True

    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Prefilled {prefilled_count} barcodes from API."))

    return product_list