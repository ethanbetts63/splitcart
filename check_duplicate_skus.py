import os
import django
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'splitcart.settings')
django.setup()

from django.db.models import Count
from companies.models import Company
from products.models import Product, Price

def find_duplicate_skus():
    """
    Finds and reports any SKUs that are linked to more than one product
    within the same company, outputting a file for each company with issues.
    """
    print("--- Starting duplicate SKU check ---")
    
    companies = Company.objects.all()
    found_any_duplicates = False

    for company in companies:
        duplicates = (
            Price.objects
            .filter(store__company=company)
            .values('sku')
            .annotate(product_count=Count('product', distinct=True))
            .filter(product_count__gt=1)
            .order_by('-product_count')
        )

        if duplicates.exists():
            found_any_duplicates = True
            
            # Sanitize company name for the report filename
            company_filename = f"{company.name.lower().replace(' ', '_')}_duplicate_skus.txt"
            report_content = []
            
            # --- Report Header ---
            report_content.append("=" * 80)
            report_content.append(f"DUPLICATE SKU REPORT FOR: {company.name.upper()}")
            report_content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_content.append("=" * 80)
            report_content.append("\n")

            for dup in duplicates:
                sku = dup['sku']
                count = dup['product_count']
                
                report_content.append("-" * 60)
                report_content.append(f"[CONFLICT] SKU: '{sku}' is linked to {count} different products.")
                report_content.append("-" * 60)
                
                conflicting_products = Product.objects.filter(
                    prices__store_product_id=sku, 
                    prices__store__company=company
                ).distinct()
                
                for i, product in enumerate(conflicting_products, 1):
                    stores = product.prices.filter(sku=sku, store__company=company).values_list('store__store_name', flat=True).distinct()
                    store_list = ", ".join(stores)
                    
                    report_content.append(f"  Product {i}:")
                    report_content.append(f"    -      ID: {product.id}")
                    report_content.append(f"    -    Name: {product.name}")
                    report_content.append(f"    -   Brand: {product.brand}")
                    report_content.append(f"    - Barcode: {product.barcode or 'N/A'}")
                    report_content.append(f"    -  Stores: {store_list}")
                    report_content.append("") # Add a blank line for readability

            # Write the generated report to a file
            try:
                with open(company_filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(report_content))
                print(f"SUCCESS: Found duplicate SKUs for '{company.name}'. Report saved to '{company_filename}'")
            except IOError as e:
                print(f"ERROR: Could not write report file for '{company.name}'. Error: {e}")


    if not found_any_duplicates:
        print("\n--- All companies have unique SKUs. No duplicates found. ---")
    
    print("\n--- SKU check finished. ---")

if __name__ == "__main__":
    find_duplicate_skus()