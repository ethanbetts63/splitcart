from companies.models import Store

def get_stores_queryset(company_slug=None, store_id=None):
    """
    Builds a queryset of stores to be processed.

    This function fetches active stores and prefetches related data to optimize 
    database access. It can filter stores by a company slug (case-insensitive name) 
    or a specific store ID.

    Args:
        company_slug (str, optional): The slug-like name of the company to filter by 
                                     (e.g., 'woolworths'). Defaults to None.
        store_id (str, optional): The specific store_id to filter by. Defaults to None.

    Returns:
        QuerySet: A Django QuerySet of Store objects.
    """
    # Start with active stores and prefetch all related data needed for the archives
    # Use select_related for the foreign key relationship to company
    queryset = Store.objects.select_related('company').filter(is_active=True).prefetch_related(
        'prices__product__category__parent', # Prefetch through the Price model
        'prices__product__substitute_goods'
    )

    # Apply filters based on arguments
    if store_id:
        queryset = queryset.filter(store_id=store_id)
    elif company_slug:
        # Use iexact for case-insensitive matching. 
        # This assumes the slug is a direct, case-insensitive match for the company name.
        queryset = queryset.filter(company__name__iexact=company_slug)

    return queryset
