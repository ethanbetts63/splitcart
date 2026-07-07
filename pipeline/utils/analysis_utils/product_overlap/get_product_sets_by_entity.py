from collections import defaultdict
from products.models import Product

def get_product_sets_by_entity(entity_type='company', company_name=None):
    """
    Fetches product sets for each company.

    Args:
        entity_type (str): only 'company' is supported.
        company_name (str, optional): Restrict results to one company name.

    Returns:
        dict: A dictionary mapping entity names to a set of product IDs.
    """
    entity_products = defaultdict(set)

    if entity_type != 'company':
        raise ValueError("Only company product sets are supported.")

    print("    Fetching all products and their company relationships...")
    queryset = Product.objects.prefetch_related('prices__company').all()
    if company_name:
        queryset = queryset.filter(prices__company__name__iexact=company_name).distinct()
    for product in queryset.iterator(chunk_size=500):
        company_names = {price.company.name for price in product.prices.all() if price.company}
        for entity_name in company_names:
            entity_products[entity_name].add(product.id)
                
    return entity_products
