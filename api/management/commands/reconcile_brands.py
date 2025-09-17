import time
from django.core.management.base import BaseCommand
from django.db import models
from products.models import Product, ProductBrand

class Command(BaseCommand):
    help = 'Uses the BrandPrefix table to find and report on products with inconsistent brand names.'

    def handle(self, *args, **options):
        start_time = time.time()
        output_file = 'brand_reconciliation_report.txt'
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Reconciliation ---"))
        self.stdout.write(f"Report will be saved to {output_file}")

        self.stdout.write("Loading and preparing brand prefixes into memory...")
        all_brands_with_prefixes = ProductBrand.objects.filter(
            models.Q(confirmed_official_prefix__isnull=False) | models.Q(longest_inferred_prefix__isnull=False)
        )

        confirmed_prefixes = []
        inferred_prefixes = []
        for brand in all_brands_with_prefixes:
            if brand.confirmed_official_prefix:
                confirmed_prefixes.append({'prefix': brand.confirmed_official_prefix, 'brand': brand})
            # Only add to inferred if there is no confirmed prefix
            elif brand.longest_inferred_prefix:
                inferred_prefixes.append({'prefix': brand.longest_inferred_prefix, 'brand': brand})
        
        # Sort both lists by prefix length in descending order
        confirmed_prefixes.sort(key=lambda x: len(x['prefix']), reverse=True)
        inferred_prefixes.sort(key=lambda x: len(x['prefix']), reverse=True)
        self.stdout.write(f"Loaded {len(confirmed_prefixes)} confirmed and {len(inferred_prefixes)} inferred brand prefixes.")

        products = Product.objects.select_related('brand').exclude(barcode__isnull=True).exclude(barcode__exact='')
        total_products = products.count()
        self.stdout.write(f"Found {total_products} products with barcodes to check...")

        # --- Pass 1: Check against CONFIRMED prefixes ---
        confirmed_discrepancies = 0
        flagged_product_ids = set()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("--- Discrepancies Found Using CONFIRMED Prefixes ---\r\n\r\n")
            for i, product in enumerate(products.iterator()):
                if (i + 1) % 2000 == 0:
                    self.stdout.write(f"  - Confirmed pass: Processed {i + 1}/{total_products} products...")

                for prefix_info in confirmed_prefixes:
                    if product.barcode.startswith(prefix_info['prefix']):
                        canonical_brand_name = prefix_info['brand'].name
                        product_brand_name = product.brand.name if product.brand else ""

                        if canonical_brand_name.lower() != product_brand_name.lower():
                            confirmed_discrepancies += 1
                            flagged_product_ids.add(product.id)
                            f.write(
                                f"Product ID {product.id}: Barcode {product.barcode} "
                                f"suggests brand '{canonical_brand_name}', but is currently '{product_brand_name}'.\r\n"
                            )
                        break # Stop after the first, most specific match

        # --- Pass 2: Check against INFERRED prefixes ---
        inferred_discrepancies = 0
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("\r\n--- Discrepancies Found Using INFERRED Prefixes ---\r\n\r\n")
            for i, product in enumerate(products.iterator()):
                if (i + 1) % 2000 == 0:
                    self.stdout.write(f"  - Inferred pass: Processed {i + 1}/{total_products} products...")

                # Skip product if it was already flagged by a more reliable confirmed prefix
                if product.id in flagged_product_ids:
                    continue

                for prefix_info in inferred_prefixes:
                    if product.barcode.startswith(prefix_info['prefix']):
                        canonical_brand_name = prefix_info['brand'].name
                        product_brand_name = product.brand.name if product.brand else ""

                        if canonical_brand_name.lower() != product_brand_name.lower():
                            inferred_discrepancies += 1
                            f.write(
                                f"Product ID {product.id}: Barcode {product.barcode} "
                                f"suggests brand '{canonical_brand_name}', but is currently '{product_brand_name}'.\r\n"
                            )
                        break # Stop after the first, most specific match
        
        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Reconciliation Complete in {duration:.2f} seconds ---"))
        self.stdout.write(f"Found {confirmed_discrepancies} discrepancies using confirmed prefixes.")
        self.stdout.write(f"Found {inferred_discrepancies} discrepancies using inferred prefixes.")
        self.stdout.write(f"Report saved to {output_file}.")
