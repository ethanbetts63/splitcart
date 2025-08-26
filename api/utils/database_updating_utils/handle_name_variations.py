
from .save_name_variation import save_name_variation

def handle_name_variations(incoming_product_details, existing_product):
    """
    Compares the names of two products with the same barcode and records
    any variations found.
    """
    incoming_name = incoming_product_details.get('name', '')
    existing_name = existing_product.name

    # Simple cleaning for a direct comparison
    cleaned_incoming_name = str(incoming_name).lower().strip()
    cleaned_existing_name = str(existing_name).lower().strip()

    if not cleaned_incoming_name or not cleaned_existing_name:
        return

    if cleaned_incoming_name != cleaned_existing_name:
        # Found a variation, save it for review
        variation_data = {
            "barcode": existing_product.barcode,
            "name_1": cleaned_incoming_name,
            "name_2": cleaned_existing_name
        }
        save_name_variation(variation_data)
