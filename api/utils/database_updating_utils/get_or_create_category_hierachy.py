from .get_or_create_category import get_or_create_category
from companies.models import Company, Category

def get_or_create_category_hierarchy(category_path: list[str], company: Company) -> Category:
    """
    Processes a product's full category path and returns the final subcategory.

    Args:
        category_path (list[str]): A list representing the category hierarchy,
            e.g., ['Pantry', 'Sauces'].
        company (Company): The company to which this hierarchy belongs.

    Returns:
        Category: The final, lowest-level Category instance in the path.
    """
    parent = None
    for category_name in category_path:
        category, _ = get_or_create_category(category_name, company, parent=parent)
        parent = category
    return parent
