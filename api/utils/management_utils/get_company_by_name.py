from companies.models.company import Company

def get_company_by_name(company_name):
    """
    Gets a company by name.
    """
    try:
        return Company.objects.get(name=company_name)
    except Company.DoesNotExist:
        return None

