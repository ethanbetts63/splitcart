from products.models import Product, Price
from .build_category_path_map import build_category_path_map

def build_product_list(store):
    """
    Builds a list of product dictionaries for a given store, including price history.
    This function is a generator that processes products in chunks to avoid database limits.

    Args:
        store (Store): The store to process products for.

    Yields:
        dict: A dictionary representing a single product and its price history.
    """
    # 1. Get all unique product IDs for the store first.
    product_ids = list(Price.objects.filter(store=store).values_list('product_id', flat=True).distinct())

    # 2. Process these IDs in manageable chunks.
    chunk_size = 500
    for i in range(0, len(product_ids), chunk_size):
        chunk_ids = product_ids[i:i + chunk_size]

        # 3. Fetch products and their category IDs for the current chunk.
        products_in_chunk = Product.objects.filter(id__in=chunk_ids).prefetch_related('category')
        prices_in_chunk = Price.objects.filter(store=store, product_id__in=chunk_ids).order_by('-scraped_at')

        # 4. Group prices by product ID for efficient lookup.
        prices_by_product = {}
        for price in prices_in_chunk:
            if price.product_id not in prices_by_product:
                prices_by_product[price.product_id] = []
            prices_by_product[price.product_id].append(price)

        # 5. Pre-fetch all category paths for the products in this chunk.
        all_category_ids = {cat.id for p in products_in_chunk for cat in p.category.all()}
        category_path_map = build_category_path_map(list(all_category_ids))

        # 6. Build and yield the final product dictionary for each product in the chunk.
        for product in products_in_chunk:
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
                    'url': product.url
                }
                cleaned_price_data = {k: v for k, v in price_data.items() if v is not None}
                price_history.append(cleaned_price_data)

            # Use the pre-fetched map for a fast lookup.
            category_paths = [category_path_map.get(cat.id) for cat in product.category.all() if category_path_map.get(cat.id)]

            product_data = {
                'name': product.name,
                'brand': product.brand,
                'sizes': product.sizes,
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
            yield cleaned_product_data
