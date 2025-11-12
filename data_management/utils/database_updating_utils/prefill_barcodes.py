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
    products_by_sku = {}
    for product_data in product_list:
        if not product_data.get('barcode'):
            sku = product_data.get('sku')
            if not sku:
                continue
            
            try:
                sku_int = int(sku)
                skus_to_lookup.add(sku_int)
                if sku_int not in products_by_sku:
                    products_by_sku[sku_int] = []
                products_by_sku[sku_int].append(product_data)
            except (ValueError, TypeError):
                continue

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
    payload = {"skus": list(skus_to_lookup)}

    if command:
        command.stdout.write(f"  - Querying API with {len(skus_to_lookup)} unique product SKUs...")

    try:
        # Use a long timeout (5 minutes) to allow for the heavy computation on the server.
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=300)
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
    for sku_str, product_api_data in api_response_map.items():
        try:
            sku_int = int(sku_str)
            if sku_int in products_by_sku:
                for product_data in products_by_sku[sku_int]:
                    if product_api_data.get('barcode'):
                        if not product_data.get('barcode'):
                            product_data['barcode'] = product_api_data['barcode']
                            prefilled_count += 1
                    if product_api_data.get('has_no_coles_barcode'):
                        product_data['has_no_coles_barcode'] = True
        except (ValueError, TypeError):
            continue

    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Successfully prefilled {prefilled_count} barcodes from API."))

    return product_list
