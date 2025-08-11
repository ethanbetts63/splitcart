from .get_or_create_category import get_or_create_category
from companies.models import Company, Category

def get_or_create_category_hierarchy(category_path: list[str], company: Company) -> Category:
    """
    Processes a product's full category path, creates the hierarchy using
    the ManyToManyField, and returns the final subcategory.
    """
    parent_obj = None
    current_category_obj = None

    for category_name in category_path:
        # Get or create the category object for the current level.
        current_category_obj, _ = get_or_create_category(category_name, company)

        # If there was a parent from the previous iteration, establish the relationship.
        if parent_obj:
            # Add the parent to the current category's list of parents.
            current_category_obj.parents.add(parent_obj)

        # The current category becomes the parent for the next iteration.
        parent_obj = current_category_obj
    
    # Return the last category processed.
    return current_category_obj
