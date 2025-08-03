# In file: stores/utils/get_or_create_category.py

"""
Finds or creates a single category instance.

This is a low-level, atomic utility that acts as a building block for creating
the full category hierarchy. It is a direct wrapper around the Django
get_or_create() method for the Category model.

Args:
    name (str): The name of the category (e.g., 'Dairy, Eggs & Fridge').
    store_obj (stores.models.Store): The store this category belongs to.
    parent_obj (companies.models.Category, optional): The parent of this category.
        Defaults to None for a top-level category.
    store_category_id (str, optional): The unique identifier for this category
        from the store's own system. Defaults to None.

Returns:
    tuple[companies.models.Category, bool]: A tuple containing:
# The found or newly created companies.models.Category instance.
        - A boolean indicating if the category was created (True) or found (False).
"""