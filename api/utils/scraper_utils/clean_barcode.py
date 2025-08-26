def clean_barcode(barcode, store_product_id=None):
    """
    Cleans a barcode value according to defined business rules.

    - Handles single or comma-separated pairs of barcodes.
    - Converts 'notfound' or empty values to None.
    - Converts 12-digit UPCs to 13-digit EANs by prepending a '0'.
    - Nullifies short barcodes if they match the store_product_id.
    - Discards barcodes that are not 12 or 13 digits long.
    """
    if not barcode or str(barcode).lower() == 'notfound':
        return None

    barcodes = [b.strip() for b in str(barcode).split(',')]
    
    valid_ean13 = None

    for b in barcodes:
        if len(b) == 13:
            valid_ean13 = b
            break  # Prefer the existing 13-digit code
        elif len(b) == 12:
            # Found a 12-digit code, convert it but keep looking for a 13-digit one
            valid_ean13 = f"0{b}"

    if valid_ean13:
        return valid_ean13

    # If no valid EAN-13 was found, check for short codes that might be store IDs
    for b in barcodes:
        if len(b) < 12:
            if store_product_id and b == str(store_product_id):
                return None  # It's an internal code, not a universal barcode
    
    # If we get here, no valid barcode was found
    return None