from products.models import Product, Price


def get_category_path(category):
    """
    Traverses up the category tree to build a full path for a given category.
    Returns a list of category names, from the top-level parent to the category itself.
    """
    print(f"          [DEBUG] get_category_path for: {category.name} ({category.id})")
    path = []
    current = category
    # Add a safeguard against potential infinite loops
    max_depth = 20
    depth = 0
    while current and depth < max_depth:
        print(f"            [DEBUG] current: {current.name} ({current.id})")
        path.insert(0, current.name)
        current = current.parents.first()
        depth += 1
    return path



def build_product_list(store):
    """
    Builds a list of product dictionaries for a given store, including price history.
    This function is a generator that processes products in chunks to avoid database limits.

    Args:
        store (Store): The store to process products for.

    Yields:
        dict: A dictionary representing a single product and its price history.
    """
    print("\n  [DEBUG] build_product_list started.")
    # 1. Get all unique product IDs for the store first.
    product_ids = list(Price.objects.filter(store=store).values_list('product_id', flat=True).distinct())
    print(f"  [DEBUG] Found {len(product_ids)} unique product IDs.")

    # 2. Process these IDs in manageable chunks.
    chunk_size = 500 # SQLite's default limit is 1000, so 500 is a safe chunk size.
    for i in range(0, len(product_ids), chunk_size):
        chunk_ids = product_ids[i:i + chunk_size]
        print(f"\n  [DEBUG] Processing chunk {i // chunk_size + 1} of {len(product_ids) // chunk_size + 1} ({len(chunk_ids)} IDs)...")

        # 3. Fetch products and prices for the current chunk.
        products_in_chunk = Product.objects.filter(id__in=chunk_ids).prefetch_related(
            'category__parents'
        )
        prices_in_chunk = Price.objects.filter(store=store, product_id__in=chunk_ids).order_by('-scraped_at')
        print("  [DEBUG] Fetched products and prices for chunk.")

        # 4. Group prices by product ID for efficient lookup.
        prices_by_product = {}
        for price in prices_in_chunk:
            if price.product_id not in prices_by_product:
                prices_by_product[price.product_id] = []
            prices_by_product[price.product_id].append(price)
        print("  [DEBUG] Grouped prices by product.")

        # 5. Build and yield the final product dictionary for each product in the chunk.
        print("  [DEBUG] Starting to build and yield products for this chunk...")
        for product in products_in_chunk:
            print(f"    [DEBUG] Building data for product: {product.id}")
            price_history = []
            for price in prices_by_product.get(product.id, []):
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
                price_history.append(cleaned_price_data)

            category_paths = []
            for cat in product.category.all():
                category_paths.append(get_category_path(cat))

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
                'price_history': price_history,
                'category_paths': category_paths
            }

            cleaned_product_data = {k: v for k, v in product_data.items() if v is not None and v != "" and v != []}
            print(f"    [DEBUG] About to yield product: {product.id}")
            yield cleaned_product_data
            print(f"    [DEBUG] Returned from yielding product: {product.id}")
