from companies.models import Company, Store

def get_store_and_company(company_name: str, store_id: str) -> tuple[Store | None, Company | None]:
    """
    Finds a Company and a Store based on their name and store_id.

    Args:
        company_name: The name of the company to find.
        store_id: The store_id to find.

    Returns:
        A tuple containing the Store object and Company object, or (None, None) if not found.
    """
    try:
        company_obj = Company.objects.get(name__iexact=company_name)
        store_obj = Store.objects.get(store_id=store_id, company=company_obj)
        return store_obj, company_obj
    except (Company.DoesNotExist, Store.DoesNotExist):
        return None, None
