import time
from django.core.management.base import BaseCommand
from products.models import Product, ProductBrand

class Command(BaseCommand):
    help = 'Uses confirmed GS1 prefixes to find and report on products with inconsistent brand names.'

    def handle(self, *args, **options):
        start_time = time.time()
        output_file = 'brand_discrepancy_report.txt'
        self.stdout.write(self.style.SUCCESS("--- Starting Brand Discrepancy Report ---"))
        self.stdout.write(f"Report will be saved to {output_file}")

        self.stdout.write("Loading brands with confirmed prefixes into memory...")
        brands_with_prefixes = ProductBrand.objects.filter(confirmed_official_prefix__isnull=False)
        
        prefix_map = {brand.confirmed_official_prefix: brand for brand in brands_with_prefixes}
        
        self.stdout.write(f"Loaded {len(prefix_map)} unique confirmed prefixes.")

        # Get all products with barcodes to check against the prefixes
        all_products = list(Product.objects.select_related('brand').exclude(barcode__isnull=True).exclude(barcode__exact=''))
        
        # Create a map of brand_id -> list of products for efficient lookup
        products_by_brand = {}
        for p in all_products:
            if p.brand_id not in products_by_brand:
                products_by_brand[p.brand_id] = []
            products_by_brand[p.brand_id].append(p)

        self.stdout.write(f"Found {len(all_products)} products with barcodes to check...")

        discrepancies_found = 0
        # Keep track of products that have already been reported as a discrepancy
        flagged_product_ids = set()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("--- Brand Discrepancies Found Using Confirmed GS1 Prefixes ---")

            # Sort prefixes by length, descending, to match most specific prefix first
            sorted_prefixes = sorted(prefix_map.keys(), key=len, reverse=True)

            for i, product in enumerate(all_products):
                if (i + 1) % 2000 == 0:
                    self.stdout.write(f"  - Processed {i + 1}/{len(all_products)} products...")
                
                if product.id in flagged_product_ids:
                    continue

                for prefix in sorted_prefixes:
                    if product.barcode.startswith(prefix):
                        canonical_brand = prefix_map[prefix]
                        product_brand = product.brand

                        # Check for discrepancy
                        if not product_brand or canonical_brand.id != product_brand.id:
                            discrepancies_found += 1
                            flagged_product_ids.add(product.id)
                            
                            # Find an example product for the canonical brand
                            canonical_products = products_by_brand.get(canonical_brand.id, [])
                            canonical_example = canonical_products[0] if canonical_products else None
                            
                            f.write(
                                f"--- Discrepancy #{discrepancies_found} ---\n"
                                f"Barcode Prefix: {prefix}\n"
                                f"Official Brand: '{canonical_brand.name}' (ID: {canonical_brand.id})\n"
                                f"Conflicting Brand: '{product_brand.name if product_brand else 'None'}' (ID: {product_brand.id if product_brand else 'N/A'})\n\n"
                            )
                            
                            if canonical_example:
                                f.write(
                                    f"  Example product for OFFICIAL brand:\n"
                                    f"    - Product ID: {canonical_example.id}\n"
                                    f"    - Name: {canonical_example.name}\n"
                                    f"    - Barcode: {canonical_example.barcode}\n\n"
                                )
                            else:
                                f.write("  No product examples found for the official brand in the current dataset.\n\n")

                            f.write(
                                f"  Example product for CONFLICTING brand:\n"
                                f"    - Product ID: {product.id}\n"
                                f"    - Name: {product.name}\n"
                                f"    - Barcode: {product.barcode}\n"
                                "----------------------------------------------------\n\n"
                            )                        
                        # Once a product has been matched to its most specific prefix, move to the next product
                        break

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"--- Report Generation Complete in {duration:.2f} seconds ---"))
        self.stdout.write(f"Found {discrepancies_found} discrepancies.")
        self.stdout.write(f"Report saved to {output_file}.")