from companies.models import Category, Company

def _build_tree_string(category, prefix="", is_last=True):
    """Recursively builds a string for a category and its children."""
    connector = "└── " if is_last else "├── "
    tree_string = f"{prefix}{connector}{category.name}\n"
    
    children = list(category.children.all().order_by('name'))
    child_count = len(children)
    
    for i, child in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        tree_string += _build_tree_string(child, prefix=new_prefix, is_last=(i == child_count - 1))
        
    return tree_string

def generate_category_tree(company_name: str):
    """
    Generates a string representation of the category tree for a given company.
    """
    try:
        company = Company.objects.get(name__iexact=company_name)
    except Company.DoesNotExist:
        return f"Error: Company '{company_name}' not found."

    root_categories = Category.objects.filter(company=company, parent__isnull=True).order_by('name')

    if not root_categories.exists():
        return f"No categories found for {company.name}."

    tree_output = f"Category Tree for {company.name}:\n"
    
    category_count = len(root_categories)
    for i, category in enumerate(root_categories):
        tree_output += _build_tree_string(category, prefix="", is_last=(i == category_count - 1))

    return tree_output
