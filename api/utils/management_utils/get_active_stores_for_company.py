from companies.models.store import Store

def get_active_stores_for_company(company):
    """
    Gets all active stores for a given company.
    """
    stores = Store.objects.filter(company=company, is_active=True)
    if not stores.exists():
        print(f"No active stores found for company '{company.name}'.")
        return None
    return stores
