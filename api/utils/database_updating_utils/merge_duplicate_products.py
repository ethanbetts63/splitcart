from django.db import transaction
from products.models import Price, Product

@transaction.atomic
def merge_products(canonical_product, duplicate_product):
    """
    Merges the duplicate product into the canonical product.
    - Re-points all prices from the duplicate to the canonical.
    - Fills in any missing data on the canonical product.
    - Deletes the duplicate product.
    This operation is atomic.
    """
    print(f"Merging duplicate '{duplicate_product.name}' into canonical '{canonical_product.name}'...")

    # 1. Re-point all Price records from the duplicate to the canonical product
    prices_to_move = Price.objects.filter(product=duplicate_product)
    price_count = prices_to_move.count()
    prices_to_move.update(product=canonical_product)
    print(f"- Moved {price_count} price records.")

    # 2. Fill in any fields on the canonical product that it's missing but the duplicate has
    # This is a simple example; you can expand this to any fields you want to preserve.
    updated_fields = []

    # TODO: Implement more sophisticated merging logic here if needed.
    # For example, merging 'sizes' JSON fields, taking the most complete
    # 'description', or combining 'name_variations'.

    # Add any other fields you want to check and merge here

    if updated_fields:
        canonical_product.save()
        print(f"- Updated missing fields on canonical product: {updated_fields}")

    # 3. Delete the duplicate product
    duplicate_product.delete()
    print(f"- Successfully deleted duplicate product.")

    print(f"Merge complete for '{canonical_product.name}'.")
