from companies.models.store import Store
from products.models.price import Price

def deactivate_prices_for_store(store: Store):
    """
    Sets all active prices for a specific store to inactive.

    This is typically run before updating the database with a fresh scrape,
    ensuring that only the newly scraped prices are marked as active.

    Args:
        store: The Store object for which to deactivate prices.
    
    Returns:
        The number of prices that were deactivated.
    """
    num_deactivated = Price.objects.filter(store=store, is_active=True).update(is_active=False)
    return num_deactivated
