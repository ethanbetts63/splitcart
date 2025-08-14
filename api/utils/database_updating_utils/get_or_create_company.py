from companies.models import Company

def get_or_create_company(company_name: str) -> Company:
    """
    Finds or creates a single Company instance.

    Args:
        company_name: The name of the company to find or create.

    Returns:
        The Company object.
    """
    company, created = Company.objects.get_or_create(
        name__iexact=company_name,
        defaults={'name': company_name.title()}
    )
    return company, created
