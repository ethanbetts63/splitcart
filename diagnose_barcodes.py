
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splitcart.settings')
django.setup()

from products.models import Product

def find_problematic_barcodes():
    """
    Inspects specific products known to be problematic canonicals
    to find out what their barcode value is.
    """
    problem_products = ['Bananas', ' Snacking Radish']
    print("--- Running diagnostic script to find problematic barcodes ---")

    for product_name in problem_products:
        print(f"\n--- Checking: {product_name.strip()} ---")
        try:
            product = Product.objects.get(name=product_name)
            barcode = product.barcode
            print(f"  - ID: {product.id}")
            print(f"  - Name: {product.name}")
            print(f"  - Barcode: '{barcode}'")

            if barcode:
                # Find how many other products share this barcode
                shared_count = Product.objects.filter(barcode=barcode).exclude(id=product.id).count()
                print(f"  - Found {shared_count} other products sharing this barcode.")
            
        except Product.DoesNotExist:
            print(f"  - Could not find a product named '{product_name}'.")
        except Product.MultipleObjectsReturned:
            print(f"  - Found multiple products named '{product_name}'. This is also an issue.")

    print("\n--- Diagnostic script finished. ---")

if __name__ == "__main__":
    find_problematic_barcodes()
