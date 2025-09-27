from products.models import Product
from scraping.data.product_translation_table import PRODUCT_NAME_TRANSLATIONS

def prefill_barcodes_from_db(product_list: list, command=None) -> list:
    """
    Iterates through a list of product dictionaries and fills in missing barcodes
    by looking for matching products in the database.

    Args:
        product_list (list): A list of product dictionaries (from a .jsonl file).
        command: Optional Django command object for logging.

    Returns:
        list: The same list, with barcode fields populated where matches were found.
    """
    if command:
        command.stdout.write(f"  - Prefilling barcodes from DB for {len(product_list)} products...")

    prefilled_count = 0
    for i, product_data in enumerate(product_list):
        # Only process products that are missing a barcode
        if not product_data.get('barcode'):
            # The normalized string is already generated in the JSONL file.
            incoming_normalized_string = product_data.get('normalized_name_brand_size')
            if not incoming_normalized_string:
                continue

            # Look up the incoming string in the translation table to find the canonical string.
            # If it's not in the table, it is its own canonical string.
            canonical_normalized_string = PRODUCT_NAME_TRANSLATIONS.get(incoming_normalized_string, incoming_normalized_string)

            # Query the database for a match using the canonical normalized string
            matching_product = Product.objects.filter(
                normalized_name_brand_size=canonical_normalized_string
            ).first()

            if matching_product:
                # If the match has a real barcode, use it.
                if matching_product.barcode:
                    product_data['barcode'] = matching_product.barcode
                    prefilled_count += 1
                # If the match is known to have no Coles barcode, mark the current product as such to prevent re-scraping.
                elif matching_product.has_no_coles_barcode:
                    product_data['barcode'] = None
    
    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Prefilled {prefilled_count} barcodes from the database."))

    return product_list
