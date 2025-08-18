from products.models import Product

def batch_create_new_products(consolidated_data: dict):
    """
    Pass 2: Identify new products and bulk create them.
    """
    print("--- Pass 2: Batch creating new products ---")
    existing_products_cache = {
        (p.name.lower() if p.name else '', p.brand.lower() if p.brand else '', p.size.lower() if p.size else ''): p 
        for p in Product.objects.all()
    }
    print(f"Found {len(existing_products_cache)} existing products.")

    new_products_to_create = []
    seen_keys = set() # Add this set to track keys already added to new_products_to_create

    for key, data in consolidated_data.items():
        if key not in existing_products_cache and key not in seen_keys: # Check seen_keys
            details = data['product_details']
            new_products_to_create.append(                Product(
                    name=str(details.get('name', '')).strip(), brand=str(details.get('brand', '')).strip(),
                    size=str(details.get('package_size', '')).strip(), barcode=details.get('barcode'),
                    image_url=details.get('image_url_main'), url=details.get('url'),
                    description=details.get('description_long'), country_of_origin=details.get('country_of_origin'),
                    ingredients=details.get('ingredients'), allergens=details.get('allergens_may_be_present')))
            seen_keys.add(key) # Add key to seen_keys

    if new_products_to_create:
        print(f"Creating {len(new_products_to_create)} new products...")
        Product.objects.bulk_create(new_products_to_create, batch_size=1000, ignore_conflicts=True)
        print("Bulk create complete.")
    else:
        print("No new products to create.")

    print("Refreshing product cache...")
    full_product_cache = {
        (p.name.lower() if p.name else '', p.brand.lower() if p.brand else '', p.size.lower() if p.size else ''): p 
        for p in Product.objects.all()
    }
    print(f"Total products in cache: {len(full_product_cache)}")
    return full_product_cache
