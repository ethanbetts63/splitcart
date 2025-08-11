from products.models import Product, Price
from companies.models import Store

def create_price(price_data: dict, product_obj: Product, store_obj: Store) -> Price:
    """
    Creates a new historical price record for a product.

    This function ALWAYS creates a new Price instance. It does not update existing
    ones. This is essential for building a complete and accurate price history
    for every product at every store.

    Args:
        price_data (dict): The dictionary for a single product from the JSON file.
        product_obj (Product): The canonical Product instance.
        store_obj (Store): The Store instance where this price was recorded.

    Returns:
        Price: The newly created Price model instance.
    """
    price = Price.objects.create(
        product=product_obj,
        store=store_obj,
        store_product_id=price_data.get('store_product_id'),
        price=price_data['price'],
        was_price=price_data.get('was_price'),
        unit_price=price_data.get('unit_price'),
        unit_of_measure=price_data.get('unit_of_measure'),
        is_on_special=price_data.get('is_on_special', False),
        is_available=price_data.get('is_available', True),
        url=price_data.get('url'),
        is_active=True  # New prices are always active
    )
    return price
