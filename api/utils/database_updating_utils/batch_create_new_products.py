from django.db import IntegrityError
from api.utils.synonym_utils.bulk_save_synonyms import bulk_save_synonyms
from api.utils.database_updating_utils.create_update_name_variation_hotlist import bulk_add_to_hotlist
from api.utils.synonym_utils.handle_barcode_match import handle_barcode_match
from api.utils.database_updating_utils.handle_name_variations import handle_name_variations
from products.models import Product, Price

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
    prices_with_ids = Price.objects.filter(store_product_id__isnull=False).exclude(sku='').select_related('product', 'store')
    for price in prices_with_ids:
        key = (price.store.store_id, price.sku)
        store_product_id_cache[key] = price.product
    command.stdout.write(f"Built cache for {len(store_product_id_cache)} store-specific product IDs.")

    # Cache 3: Normalized Name-Brand-Size String (Fallback)
    normalized_string_cache = {p.normalized_name_brand_size: p for p in all_products if p.normalized_name_brand_size}
    command.stdout.write(f"Built cache for {len(normalized_string_cache)} normalized strings.")

    # --- Step 2: Identify existing and new products ---
    product_lookup_cache = {}  # This is the final cache we will return
    products_to_create_data = []  # Store tuples of (key, data) for new products
    
    # In-memory collectors for new discoveries
    newly_discovered_synonyms = {}
    new_hotlist_entries = []

    total_products = len(consolidated_data)
    processed_count = 0
    command.stdout.write("Identifying existing vs. new products...")
    
    for key, data in consolidated_data.items():
        processed_count += 1
        command.stdout.write(f'\r  Processed {processed_count}/{total_products} products...', ending='')

        product = None
        product_details = data['product_details']
        
        # Tier 1: Match by Barcode
        barcode = product_details.get('barcode')
        if barcode and barcode in barcode_cache:
            product = barcode_cache[barcode]
            # When a barcode match is found, check for potential brand synonyms and name variations.
            new_synonym = handle_barcode_match(product_details, product)
            if new_synonym:
                newly_discovered_synonyms.update(new_synonym)
            
            hotlist_entry = handle_name_variations(product_details, product, data['company_name'])
            if hotlist_entry:
                new_hotlist_entries.append(hotlist_entry)

        # Tier 2: Match by Store Product ID
        if not product:
            store_id = data['price_history'][0].get('store_id')
            sku = product_details.get('sku')
            if store_id and sku and (store_id, sku) in store_product_id_cache:
                product = store_product_id_cache[(store_id, sku)]

        # Tier 3: Match by Normalized String
        if not product:
            normalized_string = product_details.get('normalized_name_brand_size')
            if normalized_string in normalized_string_cache:
                product = normalized_string_cache[normalized_string]

        if product:
            product_lookup_cache[key] = product
        else:
            products_to_create_data.append((key, data))

    command.stdout.write('') # Newline after progress indicator

    # --- After the loop, perform bulk saves ---
    bulk_save_synonyms(newly_discovered_synonyms)
    bulk_add_to_hotlist(new_hotlist_entries)
    command.stdout.write(f"Saved {len(newly_discovered_synonyms)} new brand synonyms and {len(new_hotlist_entries)} new name variations.")

    # --- Step 3: Batch create new products ---
    if products_to_create_data:
        command.stdout.write(f"Found {len(products_to_create_data)} potential new products.")
        new_product_objects = []
        seen_normalized_strings = set(normalized_string_cache.keys())

        for _, data in products_to_create_data:
            product_details = data['product_details']
            
            normalized_string = product_details.get('normalized_name_brand_size')

            if normalized_string and normalized_string not in seen_normalized_strings:
                # Get name variations that were consolidated
                name_variations = data.get('name_variations_to_process', [])

                # Create a Product instance with the normalized data
                new_product_objects.append(Product(
                    name=product_details.get('name', ''),
                    brand=product_details.get('brand', ''),
                    sizes=product_details.get('sizes', []),
                    barcode=product_details.get('barcode'),
                    name_variations=name_variations,  # Add the variations here
                    image_url=product_details.get('image_url_main'),
                    url=product_details.get('url'),
                    description=product_details.get('description_long'),
                    country_of_origin=product_details.get('country_of_origin'),
                    ingredients=product_details.get('ingredients'),
                    normalized_name_brand_size=normalized_string
                ))
                seen_normalized_strings.add(normalized_string)

        if new_product_objects:
            command.stdout.write(f"Creating {len(new_product_objects)} new unique products...")
            try:
                Product.objects.bulk_create(new_product_objects, batch_size=999)
            except IntegrityError as e:
                command.stderr.write(command.style.ERROR(f'\n--- DEBUG: Bulk create failed. Error: {e} ---'))
                command.stderr.write(command.style.ERROR('--- DEBUG: Finding the exact conflicting product (without new DB queries)... ---'))
                
                if 'products_product.barcode' in str(e):
                    # Get barcodes that were already in the DB at the start
                    existing_barcodes = set(barcode_cache.keys())
                    
                    # First, check if any of the "new" products have a barcode that already existed.
                    offender_found = False
                    for product_obj in new_product_objects:
                        if product_obj.barcode in existing_barcodes:
                            command.stderr.write(command.style.ERROR('--- DEBUG: CONFLICT FOUND ---'))
                            command.stderr.write(f'  - This product\'s barcode already exists in the database.')
                            command.stderr.write(f'  - Name: {product_obj.name}')
                            command.stderr.write(f'  - Barcode: {product_obj.barcode}')
                            offender_found = True
                            break
                    
                    # If not, the conflict must be a duplicate barcode within the new batch itself.
                    if not offender_found:
                        command.stderr.write(command.style.ERROR('--- DEBUG: Conflict is a duplicate barcode within this batch ---'))
                        seen_barcodes_in_batch = set()
                        for product_obj in new_product_objects:
                            if product_obj.barcode in seen_barcodes_in_batch:
                                command.stderr.write(command.style.ERROR('--- DEBUG: CONFLICT FOUND ---'))
                                command.stderr.write(f'  - This product has a barcode that is duplicated earlier in this same batch.')
                                command.stderr.write(f'  - Name: {product_obj.name}')
                                command.stderr.write(f'  - Barcode: {product_obj.barcode}')
                                break
                            if product_obj.barcode:
                                seen_barcodes_in_batch.add(product_obj.barcode)

                raise e # Re-raise the exception to halt the script as before
            
            # --- Step 4: Refresh cache with newly created products ---
            command.stdout.write("Refreshing cache with newly created products...")
            newly_created_products = Product.objects.filter(
                normalized_name_brand_size__in=[p.normalized_name_brand_size for p in new_product_objects]
            )
            new_products_cache = {p.normalized_name_brand_size: p for p in newly_created_products}

            for key, data in products_to_create_data:
                product_details = data['product_details']
                normalized_string = product_details.get('normalized_name_brand_size')

                if normalized_string in new_products_cache:
                    product_lookup_cache[key] = new_products_cache[normalized_string]

    command.stdout.write(f"Final product lookup cache contains {len(product_lookup_cache)} entries.")
    return product_lookup_cache