# In file: products/utils/get_or_create_product.py

"""
Finds a canonical product in the database or creates a new one.

This is the core logic for preventing duplicate products. It uses a tiered
matching strategy, starting with the most reliable identifiers and falling
back to less precise methods.

Args:
    product_data (dict): A dictionary representing a single product from the 
        processed JSON file. Must contain keys like 'name', 'brand', 'size',
        'barcode', and the store-specific 'stockcode'.
    store_obj (stores.models.Store): The Django model instance of the store 
        where this product was scraped (e.g., the 'coles' Store object).
    category_obj (stores.models.Category): The lowest-level category instance 
        that this product belongs to. This is only used if a new product
        needs to be created.

Returns:
    tuple[products.models.Product, bool]: A tuple containing:
        - The found or newly created products.models.Product instance.
        - A boolean indicating if the product was created (True) or found (False).

Logic Flow:
    1.  Tier 1 (Barcode): If product_data['barcode'] exists, search for a 
        Product with that barcode. If found, return it.
    2.  Tier 2 (Store-Specific ID): Search for a previous Price instance with the
        matching store_obj and store_product_id (from product_data['stockcode']).
        If found, return that price's associated product.
    3.  Tier 3 (Fuzzy Match): If no match yet, create a normalized string from
        the product's brand, name, and size. Use a library like 'thefuzz' to
        compare this string against all existing products. If a match with a
        high similarity score (e.g., > 95%) is found, return that product.
    4.  Tier 4 (Create New): If all checks fail, create a new Product instance
        using the data from product_data and the provided category_obj.
"""