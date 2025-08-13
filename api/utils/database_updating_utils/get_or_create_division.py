from companies.models import Division, Company

def get_or_create_division(company_obj: Company, division_name: str):
    """
    Gets or creates a Division object for a given Company.
    """
    division, created = Division.objects.get_or_create(
        company=company_obj,
        id=division_name,
        defaults={'name': division_name}
    )
    return division, created
