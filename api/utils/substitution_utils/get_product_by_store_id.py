
from typing import Optional

from products.models import Product, Price

def get_product_by_store_id(sku: str) -> Optional[Product]:
    """
    Finds and returns a Product object based on its sku.

    Args:
        sku: The store-specific product identifier.

    Returns:
        The Product object, or None if not found or if multiple are found.
    """
    try:
        price = Price.objects.select_related('product').get(
            sku=sku,
            is_active=True
        )
        return price.product
    except Price.DoesNotExist:
        print(f"Product with store_id {sku} not found in database.")
        return None
    except Price.MultipleObjectsReturned:
        print(f"Multiple active prices found for store_id {sku}.")
        return None
