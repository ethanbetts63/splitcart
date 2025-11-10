
from collections import defaultdict
from products.models import Product, Price
from companies.models import Company, Store
from django.db.models import OuterRef, Subquery

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
    store_map = {store.id: store.store_name for store in stores}
    
    # Get the most recent price for each product in each store
    latest_prices_subquery = Price.objects.filter(
        product=OuterRef('product'),
        store=OuterRef('store')
    ).order_by('-scraped_date').values('id')[:1]

    prices = Price.objects.filter(
        store__in=stores,
        id=Subquery(latest_prices_subquery)
    ).select_related('product', 'store')
    
    print(f"    Found {stores.count()} stores for {company_name}.")
    print(f"    Found {prices.count()} prices.")

    for price in prices:
        if price.store.id in store_map:
            store_name = store_map[price.store.id]
            store_product_prices[store_name][price.product.id] = price.price
            
    return store_product_prices
