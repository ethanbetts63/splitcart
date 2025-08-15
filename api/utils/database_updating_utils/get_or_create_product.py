"""
Finds a canonical product in the database or creates a new one.

This is the core logic for preventing duplicate products. It uses a tiered
matching strategy, starting with the most reliable identifiers and falling
back to less precise methods.
"""
from products.models import Product, Price
from companies.models import Store, Category

def get_or_create_product(product_data: dict, store_obj: Store, category_obj: Category) -> tuple[Product, bool]:
    """
    Finds a canonical product or creates a new one, ensuring the category
    is always associated.
    """
    product = None
    created = False

    # Tier 1: Match by Barcode
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

    # Tier 3: Match by Normalized Name, Brand, and Size
    if not product:
        try:
            product = Product.objects.get(
                name__iexact=product_data.get('name'),
                brand__iexact=product_data.get('brand'),
                size__iexact=product_data.get('package_size')
            )
        except Product.DoesNotExist:
            pass

    # Tier 4: Create New Product if not found
    if not product:
        product, created = Product.objects.get_or_create(
            name=product_data.get('name'),
            brand=product_data.get('brand'),
            size=product_data.get('package_size'),
            defaults={
                'barcode': product_data.get('barcode'),
                'image_url': product_data.get('image_url_main'),
                'url': product_data.get('url'),
                'description': product_data.get('description'),
                'country_of_origin': product_data.get('country_of_origin'),
                'ingredients': product_data.get('ingredients')
            }
        )

    # This now runs for ANY product, whether it was found or created
    if product:
        product.category.add(category_obj)

    return product, created
