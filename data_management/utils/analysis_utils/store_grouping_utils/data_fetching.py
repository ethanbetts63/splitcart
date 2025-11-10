from collections import defaultdict
from companies.models import Store, Company
from products.models import Price
from django.db.models import Count

def get_store_product_prices(company_name):
    """
    Fetches all stores for a given company and their product prices.
    Returns a dictionary mapping store ID to another dictionary of product ID to price.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        print(f"Company '{company_name}' not found.")
        return None, None

    stores = Store.objects.filter(company=company).annotate(product_count=Count('prices')).filter(product_count__gt=100)
    store_count = stores.count()
    if store_count < 2:
        print("Need at least 2 stores to compare.")
        return None, None

    store_map = {store.id: store for store in stores}

    # Fetch all prices for the stores in a single query
    prices = Price.objects.filter(store__in=stores).values(
        'store_id', 
        'product_id', 
        'price'
    )

    # Process prices into a nested dictionary for quick lookup
    store_price_data = defaultdict(dict)
    for price in prices:
        if price['price'] is not None:
            store_price_data[price['store_id']][price['product_id']] = price['price']

    return store_map, store_price_data
