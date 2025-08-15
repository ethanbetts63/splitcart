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
    Builds a list of product dictionaries for a given store.
    This function is a generator, yielding one fully processed product at a time.

    Args:
        store (Store): The store to process products for.

    Yields:
        dict: A dictionary representing a single product and its price history.
    """
    processed_products = {}
    price_queryset = store.prices.prefetch_related(
        'product__category__parent',
        'product__substitute_goods'
    ).all()

    # First pass: group all prices by product ID
    for price in price_queryset:
        product = price.product
        if product.id not in processed_products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'size': product.size,
                'description': product.description,
                'image_url': product.image_url,
                'country_of_origin': product.country_of_origin,
                'allergens': product.allergens,
                'ingredients': product.ingredients,
                'barcode': product.barcode,
                'price_history': [],
                'category_paths': [] # Initialize empty category paths
            }
            processed_products[product.id] = product_data

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
        cleaned_price_data = {k: v for k, v in price_data.items() if v is not None}
        processed_products[product.id]['price_history'].append(cleaned_price_data)

    # Second pass: build category paths and yield final product data
    for product_id, product_data in processed_products.items():
        # This requires another query, but it's done per product.
        # This is a trade-off for generator-based processing.
        product_obj = price_queryset.filter(product_id=product_id).first().product
        category_paths = []
        if hasattr(product_obj, 'category'):
            for cat in product_obj.category.all():
                category_paths.append(get_category_path(cat))
        product_data['category_paths'] = category_paths

        # Clean and yield the final product dictionary
        product_data.pop('id') # Remove the temporary internal ID
        cleaned_product_data = {k: v for k, v in product_data.items() if v is not None and v != "" and v != []}
        yield cleaned_product_data
