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
    fields_to_merge = {
        'barcode': {'check_conflict': True},
        'image_url': {'check_conflict': False},
        'url': {'check_conflict': False},
        'description': {'check_conflict': False},
        'country_of_origin': {'check_conflict': False},
        'allergens': {'check_conflict': False},
        'ingredients': {'check_conflict': False},
    }
    updated_fields = []

    for field_name, rules in fields_to_merge.items():
        value_to_copy = getattr(product_to_delete, field_name)
        # If the field is empty on the product we're keeping, but present on the one we're deleting...
        if not getattr(product_to_keep, field_name) and value_to_copy:
            
            # For fields that have their own unique constraints, check for conflicts before copying.
            if rules['check_conflict']:
                if Product.objects.exclude(pk=product_to_keep.pk).filter(**{field_name: value_to_copy}).exists():
                    log.append(f"WARNING: Could not merge field '{field_name}' with value '{value_to_copy}' from product {product_to_delete.id} because it's already in use.")
                    continue # Skip to the next field

            # ...copy the value over.
            setattr(product_to_keep, field_name, value_to_copy)
            updated_fields.append(field_name)

    if updated_fields:
        log.append(f"Merged fields {updated_fields} from product {product_to_delete.id} to {product_to_keep.id}.")
        if not dry_run:
            # Save only the fields that were actually updated.
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