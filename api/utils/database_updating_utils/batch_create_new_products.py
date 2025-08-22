from products.models import Product, Price
from api.utils.normalization_utils import normalize_product_data

def batch_create_new_products(command, consolidated_data: dict):
    """
    Pass 2: Identify new products using a tiered matching system and bulk create them.
    This version uses the central product_cleaning utility.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Pass 2: Batch creating new products with central cleaning utility ---"))

    # --- Step 1: Pre-fetch all data for caches ---
    all_products = list(Product.objects.all())
    
    # Cache 1: Barcode (Highest Priority)
    barcode_cache = {p.barcode: p for p in all_products if p.barcode}
    command.stdout.write(f"Built cache for {len(barcode_cache)} barcodes.")

    # Cache 2: Store-Specific Product ID
    store_product_id_cache = {}
    prices_with_ids = Price.objects.filter(store_product_id__isnull=False).exclude(store_product_id='').select_related('product', 'store')
    for price in prices_with_ids:
        key = (price.store.store_id, price.store_product_id)
        store_product_id_cache[key] = price.product
    command.stdout.write(f"Built cache for {len(store_product_id_cache)} store-specific product IDs.")

    # Cache 3: Normalized Name-Brand-Size String (Fallback)
    normalized_string_cache = {p.normalized_name_brand_size: p for p in all_products if p.normalized_name_brand_size}
    command.stdout.write(f"Built cache for {len(normalized_string_cache)} normalized strings.")

    # --- Step 2: Identify existing and new products ---
    product_lookup_cache = {}  # This is the final cache we will return
    products_to_create_data = []  # Store tuples of (key, data) for new products
    
    command.stdout.write("Identifying existing vs. new products...")
    for key, data in consolidated_data.items():
        product = None
        product_details = data['product_details']
        
        # Tier 1: Match by Barcode
        barcode = product_details.get('barcode')
        if barcode and barcode in barcode_cache:
            product = barcode_cache[barcode]

        # Tier 2: Match by Store Product ID
        if not product:
            store_id = data['price_history'][0].get('store_id')
            store_product_id = product_details.get('store_product_id')
            if store_id and store_product_id and (store_id, store_product_id) in store_product_id_cache:
                product = store_product_id_cache[(store_id, store_product_id)]

        # Tier 3: Match by Normalized String
        if not product:
            # Create a temporary dictionary to get its normalized string
            temp_product_dict = {
                'name': product_details.get('name', ''),
                'brand': product_details.get('brand', ''),
                'size': product_details.get('package_size', '')
            }
            # Use the utility to populate sizes and get the normalized string
            normalized_data = normalize_product_data(temp_product_dict)
            normalized_string = normalized_data['normalized_name_brand_size']
            
            if normalized_string in normalized_string_cache:
                product = normalized_string_cache[normalized_string]

        if product:
            product_lookup_cache[key] = product
        else:
            products_to_create_data.append((key, data))

    # --- Step 3: Batch create new products ---
    if products_to_create_data:
        command.stdout.write(f"Found {len(products_to_create_data)} potential new products.")
        new_product_objects = []
        seen_normalized_strings = set(normalized_string_cache.keys())

        for _, data in products_to_create_data:
            product_details = data['product_details']
            
            # Create a dictionary and normalize it using the utility
            temp_product_dict = {
                'name': product_details.get('name', ''),
                'brand': product_details.get('brand', ''),
                'size': product_details.get('package_size', ''),
                'barcode': product_details.get('barcode'),
                'image_url_main': product_details.get('image_url_main'),
                'url': product_details.get('url'),
                'description_long': product_details.get('description_long'),
                'country_of_origin': product_details.get('country_of_origin'),
                'ingredients': product_details.get('ingredients'),
                'allergens_may_be_present': product_details.get('allergens_may_be_present')
            }
            
            normalized_data = normalize_product_data(temp_product_dict)
            normalized_string = normalized_data['normalized_name_brand_size']

            if normalized_string and normalized_string not in seen_normalized_strings:
                # Create a Product instance with the normalized data
                new_product_objects.append(Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand', ''),
                    sizes=normalized_data.get('extracted_sizes'),
                    barcode=product_details.get('barcode'),
                    image_url=product_details.get('image_url_main'),
                    url=product_details.get('url'),
                    description=product_details.get('description_long'),
                    country_of_origin=product_details.get('country_of_origin'),
                    ingredients=product_details.get('ingredients'),
                    allergens=product_details.get('allergens_may_be_present'),
                    normalized_name_brand_size=normalized_string
                ))
                seen_normalized_strings.add(normalized_string)

        if new_product_objects:
            command.stdout.write(f"Creating {len(new_product_objects)} new unique products...")
            Product.objects.bulk_create(new_product_objects, batch_size=999, ignore_conflicts=True)
            
            # --- Step 4: Refresh cache with newly created products ---
            command.stdout.write("Refreshing cache with newly created products...")
            newly_created_products = Product.objects.filter(
                normalized_name_brand_size__in=[p.normalized_name_brand_size for p in new_product_objects]
            )
            new_products_cache = {p.normalized_name_brand_size: p for p in newly_created_products}

            for key, data in products_to_create_data:
                product_details = data['product_details']
                # Recalculate normalized string using the utility for cache lookup
                temp_product_dict = {
                    'name': product_details.get('name', ''),
                    'brand': product_details.get('brand', ''),
                    'size': product_details.get('package_size', '')
                }
                normalized_data = normalize_product_data(temp_product_dict)
                normalized_string = normalized_data['normalized_name_brand_size']

                if normalized_string in new_products_cache:
                    product_lookup_cache[key] = new_products_cache[normalized_string]

    command.stdout.write(f"Final product lookup cache contains {len(product_lookup_cache)} entries.")
    return product_lookup_cache

