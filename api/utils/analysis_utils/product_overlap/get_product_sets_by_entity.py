from collections import defaultdict
from products.models import Product
from companies.models import Company, Store

def get_product_sets_by_entity(entity_type='company', company_id=None):
    """
    Fetches product sets for each entity (company or store).

    Args:
        entity_type (str): 'company' or 'store'.
        company_id (int, optional): If entity_type is 'store', specify the company_id to get stores from.

    Returns:
        dict: A dictionary mapping entity names to a set of product IDs.
    """
    entity_products = defaultdict(set)
    
    if entity_type == 'company':
        print("    Fetching all products and their company relationships...")
        queryset = Product.objects.prefetch_related('prices__store__company').all()
        for product in queryset.iterator(chunk_size=500):
            entities = {price.store.company.name for price in product.prices.all()}
            for entity_name in entities:
                entity_products[entity_name].add(product.id)
    
    elif entity_type == 'store':
        if not company_id:
            raise ValueError("company_id must be provided when entity_type is 'store'")
        
        print(f"    Fetching all products for stores in company {company_id}...")
        stores = Store.objects.filter(company_id=company_id)
        store_map = {store.id: store.name for store in stores}
        
        queryset = Product.objects.prefetch_related('prices__store').filter(prices__store__company_id=company_id)
        
        for product in queryset.iterator(chunk_size=500):
            product_stores = {price.store.id for price in product.prices.all() if price.store.id in store_map}
            for store_id in product_stores:
                entity_products[store_map[store_id]].add(product.id)
                
    return entity_products
