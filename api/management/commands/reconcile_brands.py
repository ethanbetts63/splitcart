import time
from django.core.management.base import BaseCommand
from products.models import Product, BrandPrefix

class Command(BaseCommand):
    help = 'Uses the BrandPrefix table to find and report on products with inconsistent brand names.'

    def handle(self, *args, **options):
        start_time = time.time()
        output_file = 'brand_reconciliation_report.txt'
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Reconciliation ---"))
        self.stdout.write(f"Report will be saved to {output_file}")

        self.stdout.write("Loading brand prefixes into memory...")
        prefixes = list(BrandPrefix.objects.select_related('brand').order_by('-prefix_length'))
        
        products = Product.objects.exclude(barcode__isnull=True).exclude(barcode__exact='')
        total_products = products.count()
        self.stdout.write(f"Found {total_products} products with barcodes to check...")

        discrepancies_found = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("--- Brand Reconciliation Report ---\r\n\r\n")
            
            for i, product in enumerate(products.iterator()):
                if (i + 1) % 1000 == 0:
                    self.stdout.write(f"Processed {i + 1}/{total_products} products...")

                for prefix in prefixes:
                    if product.barcode.startswith(prefix.prefix):
                        canonical_brand_name = prefix.brand.name
                        product_brand_name = product.brand or ""

                        if canonical_brand_name.lower() != product_brand_name.lower():
                            discrepancies_found += 1
                            f.write(
                                f"Product ID {product.id}: Barcode {product.barcode} "
                                f"suggests brand '{canonical_brand_name}', but is currently '{product.brand}'.\r\n"
                            )
                        
                        break
        
        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Reconciliation Complete in {duration:.2f} seconds ---"))
        self.stdout.write(f"Found {discrepancies_found} discrepancies. Report saved to {output_file}.")
