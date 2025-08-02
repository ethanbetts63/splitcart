# In file: products/utils/create_price.py

"""
Creates a new historical price record for a product.

This function ALWAYS creates a new Price instance. It does not update existing
ones. This is essential for building a complete and accurate price history
for every product at every store.

Args:
    price_data (dict): The dictionary for a single product from the JSON file.
        This contains all the price-related fields like 'price', 'was_price',
        'unit_price', 'is_on_special', 'is_available', 'url', etc.
    product_obj (products.models.Product): The canonical Product instance to which
        this price record is associated.
    store_obj (stores.models.Store): The Store instance where this price was
        recorded.

Returns:
    products.models.Price: The newly created Price model instance after it has
        been saved to the database.
"""