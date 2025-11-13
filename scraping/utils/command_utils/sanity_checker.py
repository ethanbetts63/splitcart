import json
import os
import re
from decimal import Decimal, InvalidOperation

def _validate_product_fields(product: dict, line_number: int) -> list:
    """Helper function to validate fields within a single product dictionary."""
    errors = []
    nnbs = product.get('normalized_name_brand_size', 'N/A')

    # 1. Required Fields Check
    required_fields = ['name', 'price_current', 'normalized_name_brand_size']
    for field in required_fields:
        if product.get(field) in [None, ""]:
            errors.append(f"L{line_number} (Product: {nnbs}): Required field '{field}' is missing or empty.")

    # 2. String Length Checks
    length_checks = {
        'name': 255,
        'normalized_name_brand_size': 255,
        'size': 100,
        'barcode': 50,
    }
    for field, max_len in length_checks.items():
        value = product.get(field)
        if value and isinstance(value, str) and len(value) > max_len:
            errors.append(f"L{line_number} (Product: {nnbs}): Field '{field}' exceeds max length of {max_len}. Value: '{value[:30]}...'")

    # 3. Price Sanity and Precision Checks
    price_fields = ['price_current', 'price_was', 'unit_price']
    for field in price_fields:
        price_str = product.get(field)
        if price_str is None:
            continue
        try:
            price_val = Decimal(str(price_str))
            if not (0 <= price_val < 20000):
                errors.append(f"L{line_number} (Product: {nnbs}): Field '{field}' is out of range (0-20000): {price_val}")
            if price_val.as_tuple().exponent < -2:
                errors.append(f"L{line_number} (Product: {nnbs}): Field '{field}' has more than 2 decimal places: {price_val}")
        except InvalidOperation:
            errors.append(f"L{line_number} (Product: {nnbs}): Field '{field}' is not a valid number: '{price_str}'")

    # 4. Barcode Format Check
    barcode = product.get('barcode')
    if barcode and not re.match(r'^\d{8,18}$', str(barcode)):
        errors.append(f"L{line_number} (Product: {nnbs}): 'barcode' has invalid format (must be 8-18 digits): '{barcode}'")
        
    return errors

def run_sanity_checks(file_path: str) -> list:
    """
    Reads a .jsonl file, performs sanity checks, and overwrites the file with only the valid lines.
    Returns a list of error strings found.
    """
    all_errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
    except IOError as e:
        return [f"File Error: Could not read file. Reason: {e}"]

    if not original_lines:
        return []

    valid_lines_data = []
    
    # Pass 1: Perform all per-line validation
    for i, line in enumerate(original_lines):
        line_number = i + 1
        line_errors = []
        
        try:
            data = json.loads(line)
            product = data.get('product')
            if not product:
                line_errors.append(f"L{line_number}: Line is missing 'product' key.")
            else:
                # New check for "donation" in product name
                if 'donation' in product.get('name', '').lower():
                    line_errors.append(f"L{line_number}: Product name contains 'donation', removing line.")
                else:
                    line_errors.extend(_validate_product_fields(product, line_number))
        except json.JSONDecodeError:
            line_errors.append(f"L{line_number}: Invalid JSON format.")
        
        if line_errors:
            all_errors.extend(line_errors)
            valid_lines_data.append({'line_number': line_number, 'is_valid': False, 'data': None, 'original_line': None})
        else:
            valid_lines_data.append({'line_number': line_number, 'is_valid': True, 'data': data, 'original_line': line})

    # Pass 2: Perform file-wide consistency and uniqueness checks
    final_valid_lines = []
    seen_nnbs = set()
    seen_barcodes = set()
    seen_skus = set() # Initialize set for SKUs
    first_metadata = None

    for line_info in valid_lines_data: # Corrected typo here
        if not line_info['is_valid']:
            continue

        is_line_still_valid = True
        data = line_info['data']
        product = data['product']
        metadata = data.get('metadata')
        line_number = line_info['line_number']
        nnbs = product.get('normalized_name_brand_size')

        # Metadata consistency
        if first_metadata is None and metadata:
            first_metadata = metadata
        elif metadata and (metadata.get('store_id') != first_metadata.get('store_id') or metadata.get('company') != first_metadata.get('company')):
            all_errors.append(f"L{line_number}: Metadata mismatch. Inconsistent 'store_id' or 'company'.")
            is_line_still_valid = False

        # Uniqueness checks
        if nnbs:
            if nnbs in seen_nnbs:
                all_errors.append(f"L{line_number}: Duplicate 'normalized_name_brand_size' (keeping first occurrence): {nnbs}")
                is_line_still_valid = False
            else:
                seen_nnbs.add(nnbs)
        
        barcode = product.get('barcode')
        if barcode:
            if barcode in seen_barcodes:
                all_errors.append(f"L{line_number}: Duplicate 'barcode' (keeping first occurrence): {barcode}")
                is_line_still_valid = False
            else:
                seen_barcodes.add(barcode)
        
        # SKU uniqueness check
        sku = product.get('sku')
        if sku:
            if sku in seen_skus:
                all_errors.append(f"L{line_number}: Duplicate 'sku' (keeping first occurrence): {sku}")
                is_line_still_valid = False
            else:
                seen_skus.add(sku)

        if is_line_still_valid:
            final_valid_lines.append(line_info['original_line'])

    # Pass 3: Overwrite the original file if any lines were removed
    if len(final_valid_lines) < len(original_lines):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(final_valid_lines)
            all_errors.insert(0, f"File sanitized. Removed {len(original_lines) - len(final_valid_lines)} invalid lines.")
        except IOError as e:
            all_errors.insert(0, f"CRITICAL: Could not write sanitized file. Reason: {e}")

    return all_errors