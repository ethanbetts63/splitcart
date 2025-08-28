
from typing import Set

from companies.models import Company
from products.models import Price

def get_woolworths_product_store_ids() -> Set[str]:
    """
    Fetches all unique store_product_ids for active products sold by Woolworths.

    Returns:
        A set of unique sku strings.
    """
    try:
        woolworths_company = Company.objects.get(name="Woolworths")
    except Company.DoesNotExist:
        return set()

    prices = Price.objects.filter(
        store__company=woolworths_company,
        is_active=True
    ).values_list('sku', flat=True).distinct()

    return set(prices)
