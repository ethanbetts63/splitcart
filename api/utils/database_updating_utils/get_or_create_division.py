from companies.models import Division, Company

def get_or_create_division(company_obj: Company, division_name: str, external_id: str = None, store_finder_id: str = None):
    """
    Gets or creates a Division object for a given Company.
    """
    division, created = Division.objects.get_or_create(
        company=company_obj,
        name=division_name, # Use name for lookup
        defaults={
            'external_id': external_id,
            'store_finder_id': store_finder_id
        }
    )
    return division, created