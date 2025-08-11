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
    Finds a canonical product or creates a new one.

    Args:
        product_data (dict): A dictionary representing a single product from the 
            processed JSON file.
        store_obj (Store): The Django model instance of the store.
        category_obj (Category): The lowest-level category for the product.

    Returns:
        tuple[Product, bool]: The product instance and a boolean indicating
            if it was created.
    """
    # Tier 1: Match by Barcode
    barcode = product_data.get('barcode')
    if barcode:
        try:
            product = Product.objects.get(barcode=barcode)
            return product, False
        except Product.DoesNotExist:
            pass  # Continue to the next tier

    # Tier 2: Match by Store-Specific ID
    store_product_id = product_data.get('store_product_id')
    if store_product_id:
        try:
            # Find the most recent active price for this store-specific ID
            price = Price.objects.filter(
                store=store_obj,
                store_product_id=store_product_id,
                is_active=True
            ).latest('scraped_at')
            return price.product, False
        except Price.DoesNotExist:
            pass # Continue to the next tier

    # Tier 3: Match by Normalized Name, Brand, and Size
    try:
        product = Product.objects.get(
            name__iexact=product_data['name'],
            brand__iexact=product_data['brand'],
            size__iexact=product_data['size']
        )
        return product, False
    except Product.DoesNotExist:
        pass # Continue to the final tier

    # Tier 4: Create New Product
    product = Product.objects.create(
        name=product_data['name'],
        brand=product_data['brand'],
        size=product_data['size'],
        barcode=product_data.get('barcode'),
        image_url=product_data.get('image_url'),
        description=product_data.get('description'),
        country_of_origin=product_data.get('country_of_origin'),
        ingredients=product_data.get('ingredients')
    )
    if created:
        product.category.add(category_obj)
    return product, True
