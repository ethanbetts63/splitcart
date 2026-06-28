from collections import defaultdict
from products.models import Product
from companies.models import Company

def get_product_sets_by_entity(entity_type='company', company_name=None, state=None):
    """
    Fetches product sets for each company.

    Args:
        entity_type (str): only 'company' is supported after Store removal.
        company_name (str, optional): Restrict results to one company name.
        state (str, optional): Ignored; retained for caller compatibility.

    Returns:
        dict: A dictionary mapping entity names to a set of product IDs.
    """
    entity_products = defaultdict(set)
    
    if entity_type == 'company':
        print("    Fetching all products and their company relationships...")
        queryset = Product.objects.prefetch_related('prices__company').all()
        if company_name:
            queryset = queryset.filter(prices__company__name__iexact=company_name).distinct()
        for product in queryset.iterator(chunk_size=500):
            company_names = {price.company.name for price in product.prices.all() if price.company}
            for entity_name in company_names:
                entity_products[entity_name].add(product.id)
    
    elif entity_type == 'store':
        if company_name and not Company.objects.filter(name__iexact=company_name).exists():
            print(f"Company with name '{company_name}' not found.")
            return {}
        return get_product_sets_by_entity(entity_type='company', company_name=company_name)
                
    return entity_products
