
from django.db.models import QuerySet
from companies.models import Store

def get_product_queryset_for_store(store: Store) -> QuerySet:
    """
    Returns the base queryset of all prices for a given store, with related
    data prefetched for efficiency.

    Args:
        store: The Store object.

    Returns:
        A QuerySet of Price objects.
    """
    return store.prices.prefetch_related(
        'product__category__parent',
        'product__substitute_goods'
    ).all()
