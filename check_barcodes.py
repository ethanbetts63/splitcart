
import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splitcart.settings')
django.setup()

from products.models import Product

def check_barcodes():
    """
    Retrieves all barcodes from the Product table, sorts them,
    and writes them to a file.
    """
    print("Starting barcode check...")
    all_products = Product.objects.all()
    all_barcodes = [p.barcode for p in all_products if p.barcode]

    print(f"Found {len(all_barcodes)} barcodes.")

    # Sort barcodes alphabetically
    sorted_barcodes = sorted(all_barcodes)

    # Write to file
    output_file = 'barcodes_report.txt'
    with open(output_file, 'w') as f:
        for barcode in sorted_barcodes:
            f.write(f"{barcode}\n")

    print(f"Barcode report saved to {output_file}")

if __name__ == '__main__':
    check_barcodes()
