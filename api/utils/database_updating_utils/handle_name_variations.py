from api.utils.database_updating_utils.create_update_name_variation_hotlist import add_to_hotlist

def handle_name_variations(incoming_product_details, existing_product, company_name):
    """
    Compares product names with the same barcode. If a variation is found,
    it updates the existing product's name_variations field and adds the
    discovery to the hotlist for post-processing.
    """
    barcode = existing_product.barcode
    if not barcode or barcode == 'notfound':
        return

    incoming_name = incoming_product_details.get('name', '')
    existing_name = existing_product.name

    cleaned_incoming_name = str(incoming_name).strip()
    if not cleaned_incoming_name or not existing_name:
        return

    # Check if the names are different (case-insensitive)
    if cleaned_incoming_name.lower() != existing_name.lower():
        
        # 1. Add the new name to the existing product's name_variations list
        if not existing_product.name_variations:
            existing_product.name_variations = []
        
        # Create the new variation tuple
        new_variation_tuple = (cleaned_incoming_name, company_name)

        # Check if the tuple already exists
        if new_variation_tuple not in existing_product.name_variations:
            existing_product.name_variations.append(new_variation_tuple)
            existing_product.save()

        # 2. Add the discovery to the hotlist
        hotlist_entry = {
            'new_variation': cleaned_incoming_name,
            'canonical_name': existing_name,
            'barcode': barcode
        }
        add_to_hotlist(hotlist_entry)