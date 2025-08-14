def get_category_path(category):
    """
    Traverses up the category tree to build a full path for a given category.
    Returns a list of category names, from the top-level parent to the category itself.
    """
    path = []
    current = category
    while current:
        path.insert(0, current.name)
        # .parents.first() is used as we need a single path for representation
        current = current.parents.first()
    return path

def build_product_list(store):
    """
    Builds a list of product dictionaries for a given store, including price history.

    Args:
        store (Store): A Store object with prices and products prefetched.

    Returns:
        list: A list of product dictionaries.
    """
    processed_products = {}

    if not hasattr(store, 'prices'):
        return []

    # The prices are ordered by -scraped_at from the Price model's Meta
    for price in store.prices.all():
        product = price.product

        # If we haven't processed this product yet, create its main entry
        if product.id not in processed_products:
            product_data = {
                'name': product.name,
                'brand': product.brand,
                'size': product.size,
                'description': product.description,
                'image_url': product.image_url,
                'country_of_origin': product.country_of_origin,
                'allergens': product.allergens,
                'ingredients': product.ingredients,
                'barcode': product.barcode,
                'price_history': []
            }

            # Get category paths
            category_paths = []
            if hasattr(product, 'category'):
                for cat in product.category.all():
                    category_paths.append(get_category_path(cat))
            product_data['category_paths'] = category_paths

            processed_products[product.id] = product_data

        # Add the current price to the product's price history
        price_data = {
            'price': str(price.price),
            'was_price': str(price.was_price) if price.was_price else None,
            'unit_price': str(price.unit_price) if price.unit_price else None,
            'unit_of_measure': price.unit_of_measure,
            'is_on_special': price.is_on_special,
            'is_available': price.is_available,
            'scraped_at': price.scraped_at.isoformat(),
            'url': price.url
        }
        
        # Clean Nones from price_data before appending
        cleaned_price_data = {k: v for k, v in price_data.items() if v is not None}
        processed_products[product.id]['price_history'].append(cleaned_price_data)

    # Convert the dict of processed products to the final list
    final_product_list = []
    for product_id, product_data in processed_products.items():
        # Clean final product data from None, empty strings, or empty lists
        cleaned_product_data = {k: v for k, v in product_data.items() if v is not None and v != "" and v != []}
        final_product_list.append(cleaned_product_data)

    return final_product_list
