from companies.models import Company, Store

def get_or_create_store(company_obj: Company, store_metadata: dict) -> Store:
    """
    Finds or creates a single Store instance based on its store_id and company.

    Args:
        company_obj: The Company object this store belongs to.
        store_metadata: A dictionary containing store info like store_id and store_name.

    Returns:
        The Store object.
    """
    store_id = store_metadata.get('store_id')
    store_name = store_metadata.get('store_name', 'N/A')
    state = store_metadata.get('state')

    store_obj, created = Store.objects.get_or_create(
        store_id=store_id,
        company=company_obj,
        defaults={
            'name': store_name,
            'state': state
        }
    )
    return store_obj
