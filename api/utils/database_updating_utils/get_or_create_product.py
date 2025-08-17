"""
Finds a canonical product in the database or creates a new one.

This is the core logic for preventing duplicate products. It uses a tiered
matching strategy, starting with the most reliable identifiers and falling
back to less precise methods.
"""
from products.models import Product, Price
from companies.models import Store, Category

def get_or_create_product(product_data: dict, store_obj: Store, category_obj: Category, product_cache: dict, new_products_to_create: list) -> tuple[Product, bool]:
    """
    Finds a canonical product or creates a new one, ensuring the category
    is always associated.
    """
    product = None
    created = False

    # Create a composite key for cache lookup
    name_str = product_data.get('name', '')
    brand_str = product_data.get('brand', '')
    size_str = product_data.get('size', '')

    name = name_str.lower() if name_str else ''
    brand = brand_str.lower() if brand_str else ''
    size = size_str.lower() if size_str else ''
    composite_key = (name, brand, size)

    # Tier 0: Check cache first
    if composite_key in product_cache:
        product = product_cache[composite_key]

    # Tier 1: Match by Barcode
    if not product:
        barcode = product_data.get('barcode')
        if barcode:
            try:
                product = Product.objects.get(barcode=barcode)
            except Product.DoesNotExist:
                pass

    # Tier 2: Match by Store-Specific ID
    if not product:
        store_product_id = product_data.get('store_product_id')
        if store_product_id:
            try:
                price = Price.objects.filter(
                    store=store_obj,
                    store_product_id=store_product_id,
                    is_active=True
                ).latest('scraped_at')
                product = price.product
            except Price.DoesNotExist:
                pass

    # Tier 3: Match by Normalized Name, Brand, and Size (from DB)
    if not product:
        try:
            product = Product.objects.get(
                name__iexact=name,
                brand__iexact=brand,
                size__iexact=size
            )
        except Product.DoesNotExist:
            pass

    # Tier 4: Create New Product if not found (in memory)
    if not product:
        product = Product(
            name=product_data.get('name'),
            brand=product_data.get('brand'),
            size=product_data.get('size'),
            barcode=product_data.get('barcode'),
            image_url=product_data.get('image_url'),
            url=product_data.get('url'),
            description=product_data.get('description'),
            country_of_origin=product_data.get('country_of_origin'),
            ingredients=product_data.get('ingredients')
        )
        new_products_to_create.append(product)
        product_cache[composite_key] = product # Add to cache for subsequent lookups
        created = True

    # Category association will be handled after bulk creation
    if product and category_obj:
        # This part needs to be handled carefully after the product has an ID.
        # We can store these relationships and add them after bulk creating.
        if not hasattr(product, 'categories_to_add'):
            product.categories_to_add = set()
        product.categories_to_add.add(category_obj.id)

    return product, created