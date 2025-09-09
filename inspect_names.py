import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splitcart.settings')
django.setup()

from products.models import Product

def inspect_normalized_names(brand_name):
    """Prints the name and normalized_name for all products of a given brand."""
    print(f"--- Inspecting normalized names for brand: {brand_name} ---")
    
    products = Product.objects.filter(brand=brand_name)
    
    if not products.exists():
        print(f"No products found for brand '{brand_name}'.")
        return

    for product in products:
        print(f"  - Name: \"{product.name}\"\n    - Normalized Name: \"{product.normalized_name}\"\n")

if __name__ == '__main__':
    # We'll inspect a few common brands that should have size variants.
    inspect_normalized_names('Coca-Cola')
    inspect_normalized_names('Coles')
    inspect_normalized_names('Cadbury')
