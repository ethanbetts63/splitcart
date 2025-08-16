
from collections import defaultdict
from products.models import Product, Price
from companies.models import Company, Store

def get_product_prices_by_store(company_name=None, state=None):
    """
    Fetches product prices for each store.

    Args:
        company_name (str, optional): If provided, specify the company_name to get stores from.
        state (str, optional): If provided, specify the state to filter stores by.

    Returns:
        dict: A dictionary mapping store names to a dictionary of product IDs to prices.
    """
    store_product_prices = defaultdict(dict)
    
    if not company_name:
        raise ValueError("company_name must be provided")
    
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company with name '{company_name}' not found.")
        return {}

    print(f"    Fetching all products for stores in company {company_name}...")
    stores_query = Store.objects.filter(company=company)
    if state:
        print(f"    Filtering for state: {state}...")
        stores_query = stores_query.filter(state__iexact=state)
    
    stores = stores_query
    store_map = {store.id: store.name for store in stores}
    
    # Get the most recent price for each product in each store
    prices = Price.objects.filter(store__in=stores).order_by('product', '-scraped_at').distinct('product', 'store')

    for price in prices:
        if price.store.id in store_map:
            store_name = store_map[price.store.id]
            store_product_prices[store_name][price.product.id] = price.price
            
    return store_product_prices
