
from api.utils.synonym_utils.load_synonyms import load_synonyms
from api.utils.synonym_utils.save_synonym import save_synonym
from api.utils.synonym_utils.log_synonym import log_synonym

def handle_barcode_match(incoming_product_details, existing_product):
    """
    When a barcode match is found, this function compares the brands,
    and if they are different, it creates a new synonym.
    """
    incoming_brand = incoming_product_details.get('brand', '')
    existing_brand = existing_product.brand
    
    cleaned_incoming_brand = str(incoming_brand).lower().strip()
    cleaned_existing_brand = str(existing_brand).lower().strip()

    if not cleaned_incoming_brand or not cleaned_existing_brand:
        return

    if cleaned_incoming_brand != cleaned_existing_brand:
        # Before saving, check if this synonym relationship already exists
        # (either directly or inverted) in our synonym files.
        all_synonyms = load_synonyms()
        
        # Check if the incoming brand is already a known synonym or a canonical name
        if cleaned_incoming_brand in all_synonyms or cleaned_incoming_brand in all_synonyms.values():
            return

        # Check if the existing brand is a synonym (it should be a canonical name)
        if cleaned_existing_brand in all_synonyms:
            # This case is complex. The canonical brand is itself a synonym.
            # We should log this and probably not proceed.
            log_synonym('conflict', f"Canonical brand '{cleaned_existing_brand}' is already a synonym for '{all_synonyms[cleaned_existing_brand]}'. Skipping auto-generation for '{cleaned_incoming_brand}'.")
            return

        # If we've reached here, it's a new, non-conflicting synonym.
        # The existing product's brand is treated as the canonical name.
        new_synonym = {cleaned_incoming_brand: cleaned_existing_brand}
        
        save_synonym(new_synonym)
        log_synonym('new', f"New synonym found: '{cleaned_incoming_brand}' -> '{cleaned_existing_brand}'", new_synonym)

