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
    for key, data in consolidated_data.items():
        if key not in existing_products_cache:
            details = data['product_details']
            new_products_to_create.append(Product(
                name=details.get('name', '').strip(), brand=details.get('brand', '').strip(),
                size=details.get('size', '').strip(), barcode=details.get('barcode'),
                image_url=details.get('image_url'), url=details.get('url'),
                description=details.get('description'), country_of_origin=details.get('country_of_origin'),
                ingredients=details.get('ingredients')))

    if new_products_to_create:
        print(f"Creating {len(new_products_to_create)} new products...")
        Product.objects.bulk_create(new_products_to_create, batch_size=1000)
        print("Bulk create complete.")
    else:
        print("No new products to create.")

    print("Refreshing product cache...")
    full_product_cache = {(p.name.lower(), p.brand.lower(), p.size.lower()): p for p in Product.objects.all()}
    print(f"Total products in cache: {len(full_product_cache)}")
    return full_product_cache
