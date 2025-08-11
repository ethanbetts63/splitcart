def _parse_aldi_path(product_data):
    """Parses category from a raw Aldi product."""
    path = []
    categories = product_data.get('categories', [])
    for category in categories:
        name = category.get('name')
        if name:
            path.append(name.strip().title())
    return path

def _parse_coles_path(product_data):
    """Parses category from a raw Coles product."""
    path = []
    # onlineHeirs seems to be the most reliable and user-facing hierarchy
    online_heirs = product_data.get('onlineHeirs', [])
    if not online_heirs:
        return []

    # The hierarchy is typically subCategory -> category -> aisle
    heir = online_heirs[0]
    sub_cat = heir.get('subCategory')
    cat = heir.get('category')
    aisle = heir.get('aisle')
    
    if sub_cat:
        path.append(sub_cat.strip().title())
    if cat:
        path.append(cat.strip().title())
    if aisle:
        path.append(aisle.strip().title())
        
    return path

def _parse_iga_path(product_data):
    """Parses category from a raw IGA product."""
    categories = product_data.get('categories', [])
    if not categories:
        return []
    
    # The last category in the list has the full breadcrumb
    last_category = categories[-1]
    breadcrumb = last_category.get('categoryBreadcrumb', '')
    
    return [part.strip().title() for part in breadcrumb.split('/') if part]

def _parse_woolworths_path(product_data):
    """Parses category from a raw Woolworths product."""
    path = []
    attrs = product_data.get('AdditionalAttributes', {})
    
    # Constructing path from SAP fields, which are the most detailed
    dept = attrs.get('sapdepartmentname')
    cat = attrs.get('sapcategoryname')
    sub_cat = attrs.get('sapsubcategoryname')
    segment = attrs.get('sapsegmentname')

    if dept:
        path.append(dept)
    if cat:
        # This field can sometimes contain multiple levels
        path.extend([part.strip() for part in cat.split('/')])
    if sub_cat:
        path.append(sub_cat)
    if segment:
        path.append(segment)
        
    return [part.strip().title() for part in path if part]

def get_category_path(product_data: dict, company_name: str) -> list[str]:
    """
    Acts as a router to the correct parser based on the company name.
    
    Args:
        product_data: The raw dictionary for a single product.
        company_name: The name of the company.

    Returns:
        A list of strings representing the cleaned category hierarchy.
    """
    parser_map = {
        'aldi': _parse_aldi_path,
        'coles': _parse_coles_path,
        'iga': _parse_iga_path,
        'woolworths': _parse_woolworths_path
    }
    
    parser = parser_map.get(company_name.lower())
    
    if parser:
        return parser(product_data)
    else:
        return []
