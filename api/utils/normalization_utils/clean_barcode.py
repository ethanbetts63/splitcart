def clean_barcode(barcode, store_product_id=None):
    """
    Cleans a barcode value according to defined business rules.

    - Handles single or comma-separated pairs of barcodes.
    - Converts 'notfound', 'null', or empty values to None.
    - Converts 12-digit UPCs to 13-digit EANs by prepending a '0'.
    - Nullifies short barcodes if they match the store_product_id.
    - Discards barcodes that are not 12 or 13 digits long.
    - Strips leading/trailing whitespace.
    """
    if not barcode:
        return None

    # Convert to string and strip whitespace from the whole string first
    barcode_str = str(barcode).strip().lower()

    if barcode_str == 'notfound' or barcode_str == 'null':
        return None

    # Split and strip individual barcodes
    barcodes = [b.strip() for b in barcode_str.split(',')]
    
    valid_ean13 = None
    found_12_digit = None

    # Prioritize finding a 13-digit EAN
    for b in barcodes:
        if len(b) == 13 and b.isdigit():
            valid_ean13 = b
            break  # Found the best possible match
        elif len(b) == 12 and b.isdigit():
            # Keep the first 12-digit code we find, but keep looking for a 13-digit one
            if not found_12_digit:
                found_12_digit = f"0{b}"

    # If we found a 13-digit EAN, use it. Otherwise, use the converted 12-digit one.
    if valid_ean13:
        return valid_ean13
    if found_12_digit:
        return found_12_digit

    # If no valid EAN-13 was found after checking all parts, check for short codes
    # that might be internal store IDs. This part of the logic is kept from before.
    for b in barcodes:
        if len(b) < 12:
            if store_product_id and b == str(store_product_id):
                return None  # It's an internal code, not a universal barcode
    
    # If we get here, no valid 12 or 13-digit barcode was found in any part
    return None
