import os
from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Product

def find_longest_common_prefix(strs):
    if not strs:
        return ""
    strs = [s for s in strs if isinstance(s, str)]
    if not strs:
        return ""
    shortest_str = min(strs, key=len)
    for i, char in enumerate(shortest_str):
        for other_str in strs:
            if other_str[i] != char:
                return shortest_str[:i]
    return shortest_str

class Command(BaseCommand):
    help = 'Analyzes product barcodes to find common prefixes for brands and saves the report to a file.'

    def handle(self, *args, **options):
        output_file = 'prefix_analysis.txt'
        self.stdout.write(self.style.SUCCESS("--- Starting Barcode Prefix Analysis ---"))
        self.stdout.write(f"Results will be saved to {output_file}")

        brands_with_multiple_products = Product.objects.values('brand').annotate(product_count=Count('id')).filter(product_count__gt=5).order_by('-product_count')

        if not brands_with_multiple_products:
            self.stdout.write("No brands found with more than 5 products.")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("--- Barcode Prefix Analysis Results ---")

            for brand_data in brands_with_multiple_products:
                brand_name = brand_data['brand']
                product_count = brand_data['product_count']

                if not brand_name:
                    continue

                products = Product.objects.filter(brand=brand_name).exclude(barcode__isnull=True).exclude(barcode__exact='')
                barcodes = [p.barcode for p in products]

                if len(barcodes) < 2:
                    continue

                common_prefix = find_longest_common_prefix(barcodes)

                plausible_prefixes = [common_prefix[:i] for i in range(6, min(len(common_prefix), 11) + 1)]

                if plausible_prefixes:
                    f.write(f"Brand: {brand_name} ({len(barcodes)} products with barcodes)")
                    f.write(f"  Sample Barcode: {barcodes[0]}")
                    f.write(f"  Plausible Prefixes:")
                    for prefix in plausible_prefixes:
                        f.write(f"    - {prefix} (Length: {len(prefix)}")
                    f.write("-" * 40 + "")

        self.stdout.write(self.style.SUCCESS(f"--- Analysis Complete. Results saved to {output_file} ---"))
