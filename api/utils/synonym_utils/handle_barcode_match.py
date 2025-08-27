from api.utils.synonym_utils.load_synonyms import load_synonyms
def handle_barcode_match(incoming_product_details, existing_product):
    """
    When a barcode match is found, this function compares the brands.
    If they are different and not already known, it returns a new synonym pair.
    """
    incoming_brand = incoming_product_details.get('brand', '')
    existing_brand = existing_product.brand

    # For a consistent comparison, we clean the brand names by making them lowercase
    # and stripping leading/trailing whitespace.
    cleaned_incoming_brand = str(incoming_brand).lower().strip()
    cleaned_existing_brand = str(existing_brand).lower().strip()

    if not cleaned_incoming_brand or not cleaned_existing_brand:
        return None

    if cleaned_incoming_brand != cleaned_existing_brand:
        all_synonyms = load_synonyms()
        
        # Check if this relationship is already known.
        if cleaned_incoming_brand in all_synonyms and all_synonyms[cleaned_incoming_brand] == cleaned_existing_brand:
            return None
        if cleaned_existing_brand in all_synonyms and all_synonyms[cleaned_existing_brand] == cleaned_incoming_brand:
            return None
        if cleaned_incoming_brand == cleaned_existing_brand:
            return None

        # Return the new synonym pair to be collected.
        return {cleaned_incoming_brand: cleaned_existing_brand}
    
    return None