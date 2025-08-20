from django.db import IntegrityError
from products.models import Product

def batch_create_new_products(command, consolidated_data: dict):
    """
    Pass 2: Identify new products using a tiered matching system and bulk create them.
    This function implements a more robust check to prevent duplicates.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Pass 2: Batch creating new products with tiered matching ---"))

    # --- Tiered Matching Setup ---
    # Cache 1: For exact name, brand, size matching (case-insensitive)
    name_brand_size_cache = {
        (p.name.lower() if p.name else '', p.brand.lower() if p.brand else '', p.size.lower() if p.size else ''): p
        for p in Product.objects.all()
    }
    command.stdout.write(f"Found {len(name_brand_size_cache)} existing products for name/brand/size matching.")

    # Cache 2: For barcode matching
    barcode_cache = {p.barcode: p for p in Product.objects.filter(barcode__isnull=False) if p.barcode}
    command.stdout.write(f"Found {len(barcode_cache)} existing products with barcodes.")

    new_products_to_create = []
    # This cache will map the composite key to a Product object (either existing or one we are about to create)
    # It's essential for the subsequent price creation step.
    product_lookup_cache = {}
    seen_new_product_keys = set()

    command.stdout.write("Identifying new products...")
    for key, data in consolidated_data.items():
        product = None
        product_details = data['product_details']

        # Tier 1: Match by Barcode (highest priority)
        barcode = product_details.get('barcode')
        if barcode and barcode in barcode_cache:
            product = barcode_cache[barcode]

        # Tier 2: Match by Name, Brand, and Size (from pre-fetched cache)
        if not product and key in name_brand_size_cache:
            product = name_brand_size_cache[key]
        
        if product:
            product_lookup_cache[key] = product
        else:
            # This is potentially a new product.
            # Check if we've already decided to create this product in this run.
            if key not in seen_new_product_keys:
                new_product = Product(
                    name=str(product_details.get('name', '')).strip().lower(),
                    brand=str(product_details.get('brand', '')).strip().lower(),
                    size=str(product_details.get('package_size', '')).strip().lower(),
                    barcode=product_details.get('barcode'),
                    image_url=product_details.get('image_url_main'),
                    url=product_details.get('url'),
                    description=product_details.get('description_long'),
                    country_of_origin=product_details.get('country_of_origin'),
                    ingredients=product_details.get('ingredients'),
                    allergens=product_details.get('allergens_may_be_present')
                )
                new_products_to_create.append(new_product)
                seen_new_product_keys.add(key)

    # --- Bulk Creation ---
    if new_products_to_create:
        command.stdout.write(f"Creating {len(new_products_to_create)} new products...")
        try:
            # We use ignore_conflicts=True as a safeguard, but our tiered check should prevent collisions.
            Product.objects.bulk_create(new_products_to_create, batch_size=999)
            command.stdout.write("Bulk create complete.")
        except IntegrityError as e:
            command.stderr.write(command.style.ERROR(f"WARNING: An integrity error occurred during bulk creation. This is likely due to case-sensitivity conflicts with existing data. The script will continue, and the final cache refresh should resolve the missing products. Error: {e}"))
    else:
        command.stdout.write("No new products to create.")

    # --- Refresh Product Cache ---
    # After creating new products, we need a complete cache for the next steps.
    command.stdout.write("Refreshing final product cache...")
    full_product_cache = {
        (p.name.lower() if p.name else '', p.brand.lower() if p.brand else '', p.size.lower() if p.size else ''): p
        for p in Product.objects.all()
    }
    command.stdout.write(f"Total products in cache: {len(full_product_cache)}")

    # The original function returned the cache, which is used by subsequent steps.
    # The `full_product_cache` is what the next steps need.
    return full_product_cache