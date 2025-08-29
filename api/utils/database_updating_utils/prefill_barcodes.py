from products.models import Product
from api.utils.normalizer import ProductNormalizer

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
            original_name = product_data.get('name', '')
            # Use the normalizer to find the canonical name and generate the lookup key
            canonical_name = ProductNormalizer.get_canonical_name(original_name)
            
            # Create a temporary dictionary for the normalizer
            # The normalizer expects 'package_size', but the JSONL has 'size'
            temp_data_for_norm = {
                'name': canonical_name,
                'brand': product_data.get('brand', ''),
                'package_size': product_data.get('size', '') 
            }
            
            normalizer = ProductNormalizer(temp_data_for_norm)
            normalized_key = normalizer.get_normalized_string()

            if not normalized_key:
                continue

            # Query the database for a match with a barcode
            matching_product = Product.objects.filter(
                normalized_name_brand_size=normalized_key,
                barcode__isnull=False
            ).exclude(barcode='').first()

            if matching_product:
                if command and (i % 50 == 0): # Log progress periodically
                    command.stdout.write(f"    - Found barcode for \"{original_name}\" -> \"{matching_product.name}\")
                product_data['barcode'] = matching_product.barcode
                prefilled_count += 1
    
    if command:
        command.stdout.write(command.style.SUCCESS(f"  - Prefilled {prefilled_count} barcodes from the database."))

    return product_list
