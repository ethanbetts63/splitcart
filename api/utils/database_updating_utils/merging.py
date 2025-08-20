from products.models import Product, Price

def merge_duplicate_products(product_to_keep, product_to_delete, dry_run=False):
    """
    Merges two duplicate products.

    - Copies missing information from product_to_delete to product_to_keep.
    - Re-assigns prices from product_to_delete to product_to_keep.
    - Deletes the product_to_delete.

    Returns a list of log messages detailing the actions taken.
    """
    log = []

    # 1. Merge fields by copying missing data
    fields_to_merge = [
        'barcode', 'image_url', 'url', 'description', 
        'country_of_origin', 'allergens', 'ingredients'
    ]
    updated_fields = []

    for field_name in fields_to_merge:
        # If the field is empty on the product we're keeping, but present on the one we're deleting...
        if not getattr(product_to_keep, field_name) and getattr(product_to_delete, field_name):
            # ...copy the value over.
            setattr(product_to_keep, field_name, getattr(product_to_delete, field_name))
            updated_fields.append(field_name)

    if updated_fields:
        log.append(f"Merged fields {updated_fields} from product {product_to_delete.id} to {product_to_keep.id}.")
        if not dry_run:
            product_to_keep.save(update_fields=updated_fields)

    # 2. Re-parent prices from the deleted product to the kept product
    prices_to_move = Price.objects.filter(product=product_to_delete)
    price_count = prices_to_move.count()
    if price_count > 0:
        log.append(f"Moving {price_count} price records from product {product_to_delete.id} to {product_to_keep.id}.")
        if not dry_run:
            prices_to_move.update(product=product_to_keep)

    # 3. Delete the duplicate product record
    log.append(f"Deleting duplicate product {product_to_delete.id} ('{product_to_delete.name}').")
    if not dry_run:
        product_to_delete.delete()

    return log
