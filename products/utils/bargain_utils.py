from collections import defaultdict
from products.models import Price

def calculate_bargains(product_ids, company_ids):
    """
    Calculates bargain information for a given set of products and companies.

    Args:
        product_ids (list[int]): A list of product IDs to check for bargains.
        company_ids (list[int]): A list of company IDs to use for price comparisons.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a
                    bargain and contains 'product_id', 'discount', 
                    'cheaper_company_name'.
    """
    if not product_ids or not company_ids:
        return []

    # Fetch all relevant prices in a single query
    live_prices = Price.objects.filter(
        product_id__in=product_ids,
        company_id__in=company_ids
    ).select_related('company')

    # Group prices by product_id
    products_with_prices = defaultdict(list)
    for price in live_prices:
        products_with_prices[price.product_id].append(price)

    calculated_bargains = []
    for product_id, prices in products_with_prices.items():
        # A bargain requires at least two different prices to compare
        if len(prices) < 2:
            continue
        
        price_company_ids = {p.company_id for p in prices}
        if len(price_company_ids) < 2:
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
            'cheaper_company_name': min_price_obj.company.name,
        })

    return calculated_bargains
