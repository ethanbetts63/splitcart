# In file: stores/utils/get_or_create_category_hierarchy.py

"""
Processes a product's full category path and returns the final subcategory.

This function orchestrates the creation of a category hierarchy (e.g.,
Department -> Category -> Subcategory) by repeatedly calling the
get_or_create_category utility for each level.

Args:
    category_data (dict): A dictionary from the JSON containing the category
        path. Expected to have keys like 'departments', 'categories', and
        'subcategories', where each is a list of dicts with 'name' and 'id'.
    store_obj (stores.models.Store): The store to which this hierarchy belongs.

Returns:
    companies.models.Category: The final, lowest-level Category instance in the
        path (typically the subcategory). This is the object that should be
        linked to the Product. Returns None if the path is empty.
"""