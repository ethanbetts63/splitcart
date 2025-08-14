
from products.models import Product

def link_products_as_substitutes(product_a: Product, product_b: Product):
    """
    Creates a symmetrical substitute relationship between two products.

    Args:
        product_a: The first product.
        product_b: The second product.
    """
    product_a.substitute_goods.add(product_b)
