# In file: products/utils/get_woolworths_substitutes.py

"""
Enriches woolworths products with substitute goods information.

This is a post-processing utility that should be run separately from the main
data import (e.g., as a nightly or weekly management command). It queries an
external API for substitute data and updates the `substitute_goods` relationship.

Args:
    product_ids (list[int], optional): A list of specific Product primary keys
        to process. If not provided, the function can be configured to query
        all products from woolworths that haven't been updated recently.

Returns:
    None: This function modifies the database directly and does not need to
        return a value. It should log its progress and any errors.

Logic Flow:
    1.  Identify the target woolworths products to process.
    2.  For each product, call the external woolworths substitutes API.
    3.  Handle API errors gracefully.
    4.  For each substitute returned by the API, find the corresponding
        Product object in the local database (e.g., by barcode).
    5.  If the substitute product exists locally, add it to the `substitute_goods`
        ManyToManyField of the original product.
"""