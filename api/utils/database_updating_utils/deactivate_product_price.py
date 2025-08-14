
from companies.models import Store
from products.models import Product, Price

def deactivate_product_price(product: Product, store: Store):
    """
    Sets all active prices for a specific product at a specific store to inactive.

    Args:
        product: The Product object to deactivate prices for.
        store: The Store object where the prices are located.
    
    Returns:
        The number of prices that were deactivated.
    """
    num_deactivated = Price.objects.filter(
        product=product, 
        store=store, 
        is_active=True
    ).update(is_active=False)
    return num_deactivated
