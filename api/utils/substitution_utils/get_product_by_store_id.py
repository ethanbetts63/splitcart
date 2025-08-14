
from typing import Optional

from products.models import Product, Price

def get_product_by_store_id(store_product_id: str) -> Optional[Product]:
    """
    Finds and returns a Product object based on its store_product_id.

    Args:
        store_product_id: The store-specific product identifier.

    Returns:
        The Product object, or None if not found or if multiple are found.
    """
    try:
        price = Price.objects.select_related('product').get(
            store_product_id=store_product_id,
            is_active=True
        )
        return price.product
    except Price.DoesNotExist:
        print(f"Product with store_id {store_product_id} not found in database.")
        return None
    except Price.MultipleObjectsReturned:
        print(f"Multiple active prices found for store_id {store_product_id}.")
        return None
