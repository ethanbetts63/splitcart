import requests
import json
from django.conf import settings


def prefill_barcodes_from_api(product_list: list, command=None, dev: bool = False) -> list:
    """
    Enriches a list of product dictionaries with barcode info by calling a dedicated API endpoint using SKUs.
    """
    if command:
        command.stdout.write(f"  - Prefilling barcodes via API for {len(product_list)} products...")

    # Step 1: Identify products that need a lookup (have a SKU but no barcode).
    skus_to_lookup = set()
    # This dictionary maps a SKU to a list of product dicts that have that SKU
    products_by_sku = {}
    for product_data in product_list:
        # We only need to look up products that don't already have a barcode.
        if not product_data.get('barcode'):
            sku = product_data.get('sku')
            if not sku:
                continue
            
            # Use the SKU as a number, not a string, for lookup and internal mapping.
            skus_to_lookup.add(sku)
            if sku not in products_by_sku:
                products_by_sku[sku] = []
            products_by_sku[sku].append(product_data)

    if not skus_to_lookup:
        if command:
            command.stdout.write("  - No products required barcode prefilling.")
        return product_list

    # Step 2: Call the API to get barcode info for the collected SKUs.
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

    # Batch SKUs to avoid long running queries and timeouts
    batch_size = 200
    sku_list = list(skus_to_lookup)
    api_response_map = {}

    if command:
        command.stdout.write(f"  - Querying API with {len(sku_list)} unique product SKUs in batches of {batch_size}...")

    for i in range(0, len(sku_list), batch_size):
        batch = sku_list[i:i + batch_size]
        payload = {"skus": batch}
        
        if command:
            command.stdout.write(f"    - Sending batch {i//batch_size + 1}/{(len(sku_list) + batch_size - 1)//batch_size} ({len(batch)} SKUs)")

        try:
            # Increased timeout to 60 seconds for more complex queries
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            response.raise_for_status()
            api_response_map.update(response.json())
        except requests.exceptions.RequestException as e:
            if command:
                command.stdout.write(command.style.ERROR(f"    - API call for batch failed: {e}"))
            # Continue with other batches
            continue
    
    if command:
        command.stdout.write(f"  - API returned data for a total of {len(api_response_map)} products.")

    # Step 3: Update the product list with the data received from the API.
    prefilled_count = 0
    for sku, product_api_data in api_response_map.items():
        if sku in products_by_sku:
            # Update all products in the original list that share this SKU
            for product_data in products_by_sku[sku]:
                if product_api_data.get('barcode'):
                    product_data['barcode'] = product_api_data['barcode']
                    prefilled_count += 1
                if product_api_data.get('has_no_coles_barcode'):
                    product_data['has_no_coles_barcode'] = True

    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Prefilled {prefilled_count} barcodes from API."))

    return product_list