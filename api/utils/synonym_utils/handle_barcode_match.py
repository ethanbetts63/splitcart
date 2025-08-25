from api.utils.synonym_utils.load_synonyms import load_synonyms
from api.utils.synonym_utils.save_synonym import save_synonym
from api.utils.synonym_utils.log_synonym import log_synonym

def handle_barcode_match(incoming_product_details, existing_product):
    """
    When a barcode match is found, this function compares the brands,
    and if they are different, it creates a new synonym.
    """
    incoming_brand = incoming_product_details.get('brand', '')
    incoming_barcode = incoming_product_details.get('barcode', '')
    existing_brand = existing_product.brand
    existing_barcode = existing_product.barcode

    # Do not generate synonyms for products with "notfound" barcodes.
    if incoming_barcode == 'notfound' or existing_barcode == 'notfound':
        return

    # For a consistent comparison, we clean the brand names by making them lowercase
    # and stripping leading/trailing whitespace.
    cleaned_incoming_brand = str(incoming_brand).lower().strip()
    cleaned_existing_brand = str(existing_brand).lower().strip()

    if not cleaned_incoming_brand or not cleaned_existing_brand:
        return

    if cleaned_incoming_brand != cleaned_existing_brand:
        all_synonyms = load_synonyms()
        
        # Check for existing synonyms using the clean brand names
        if cleaned_incoming_brand in all_synonyms or cleaned_incoming_brand in all_synonyms.values():
            return

        if cleaned_existing_brand in all_synonyms:
            return

        # For debugging, format the output with barcodes
        key_with_barcode = f"{cleaned_incoming_brand} ({incoming_barcode})"
        value_with_barcode = f"{cleaned_existing_brand} ({existing_barcode})"

        new_synonym = {key_with_barcode: value_with_barcode}
        
        save_synonym(new_synonym)
        log_synonym('info', f"NEW SYNONYM DETECTED: {new_synonym}")