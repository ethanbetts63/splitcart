from collections import defaultdict
from products.models import Price

def calculate_bargains(product_ids, store_ids):
    """
    Calculates bargain information for a given set of products and stores.

    Args:
        product_ids (list[int]): A list of product IDs to check for bargains.
        store_ids (list[int]): A list of store IDs to use for price comparisons.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a
                    bargain and contains 'product_id', 'discount', 
                    'cheaper_store_name', and 'cheaper_company_name'.
    """
    if not product_ids or not store_ids:
        return []

    # Fetch all relevant prices in a single query
    live_prices = Price.objects.filter(
        product_id__in=product_ids,
        store_id__in=store_ids
    ).select_related('store__company')

    # Group prices by product_id
    products_with_prices = defaultdict(list)
    for price in live_prices:
        products_with_prices[price.product_id].append(price)

    calculated_bargains = []
    for product_id, prices in products_with_prices.items():
        # A bargain requires at least two different prices to compare
        if len(prices) < 2:
            continue
        
        # A bargain must be between different companies or between different IGA stores
        company_ids = {p.store.company_id for p in prices}
        is_iga = any(p.store.company.name.lower() == 'iga' for p in prices)
        iga_stores = {p.store_id for p in prices if p.store.company.name.lower() == 'iga'}
        
        if len(company_ids) < 2 and (not is_iga or len(iga_stores) < 2):
            continue

        min_price_obj = min(prices, key=lambda p: p.price)
        max_price_obj = max(prices, key=lambda p: p.price)

        # If min and max prices are the same, it's not a bargain
        if min_price_obj.price == max_price_obj.price:
            continue

        # Calculate discount percentage
        try:
            actual_discount = int(((max_price_obj.price - min_price_obj.price) / max_price_obj.price) * 100)
        except ZeroDivisionError:
            continue
        
        # We only care about bargains between 5% and 70%
        if not (5 <= actual_discount <= 70):
            continue
        
        calculated_bargains.append({
            'product_id': product_id,
            'discount': actual_discount,
            'cheaper_store_name': min_price_obj.store.store_name,
            'cheaper_company_name': min_price_obj.store.company.name,
        })

    return calculated_bargains
