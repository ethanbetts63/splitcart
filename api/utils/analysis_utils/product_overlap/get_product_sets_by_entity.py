from collections import defaultdict
from products.models import Product
from companies.models import Company, Store

def get_product_sets_by_entity(entity_type='company', company_name=None, state=None):
    """
    Fetches product sets for each entity (company or store).

    Args:
        entity_type (str): 'company' or 'store'.
        company_name (str, optional): If entity_type is 'store', specify the company_name to get stores from.
        state (str, optional): If entity_type is 'store', specify the state to filter stores by.

    Returns:
        dict: A dictionary mapping entity names to a set of product IDs.
    """
    entity_products = defaultdict(set)
    
    if entity_type == 'company':
        print("    Fetching all products and their company relationships...")
        queryset = Product.objects.prefetch_related('price_records__price_entries__store__company').all()
        for product in queryset.iterator(chunk_size=500):
            entities = set()
            for price_record in product.price_records.all():
                for price_entry in price_record.price_entries.all():
                    if price_entry.store and price_entry.store.company:
                        entities.add(price_entry.store.company.name)
            for entity_name in entities:
                entity_products[entity_name].add(product.id)
    
    elif entity_type == 'store':
        if not company_name:
            raise ValueError("company_name must be provided when entity_type is 'store'")
        
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
        
        stores = list(stores_query)
        store_map = {store.id: store.store_name for store in stores}
        
        queryset = Product.objects.prefetch_related('price_records__price_entries__store').filter(price_records__price_entries__store__in=stores).distinct()
        
        for product in queryset.iterator(chunk_size=500):
            product_stores = set()
            for price_record in product.price_records.all():
                for price_entry in price_record.price_entries.all():
                    if price_entry.store_id in store_map:
                        product_stores.add(price_entry.store_id)
            for store_id in product_stores:
                entity_products[store_map[store_id]].add(product.id)
                
    return entity_products