def handle_name_variations(incoming_product_details, existing_product, company_name):
    """
    Compares product names with the same barcode. If a variation is found,
    it updates the existing product's name_variations field and returns the
    discovery to be added to the hotlist.
    """
    barcode = existing_product.barcode
    if not barcode or barcode == 'notfound':
        return None

    incoming_name = incoming_product_details.get('name', '')
    existing_name = existing_product.name

    cleaned_incoming_name = str(incoming_name).strip()
    if not cleaned_incoming_name or not existing_name:
        return None

    # Check if the names are different (case-insensitive)
    if cleaned_incoming_name.lower() != existing_name.lower():
        
        # 1. Add the new name to the existing product's name_variations list
        if not existing_product.name_variations:
            existing_product.name_variations = []
        
        new_variation_tuple = (cleaned_incoming_name, company_name)

        if new_variation_tuple not in existing_product.name_variations:
            existing_product.name_variations.append(new_variation_tuple)

        # 2. Return the discovery to be added to the hotlist
        hotlist_entry = {
            'new_variation': cleaned_incoming_name,
            'canonical_name': existing_name,
            'barcode': barcode
        }
        return hotlist_entry
    
    return None