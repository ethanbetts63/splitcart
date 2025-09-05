import os
from django.core.management.base import BaseCommand
from django.db.models import Count
from products.models import Product

def find_longest_common_prefix(strs):
    if not strs:
        return ""
    # Ensure all items are strings and not None
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
    help = 'Analyzes product barcodes to find common prefixes for brands.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Barcode Prefix Analysis ---"))

        # Get brands with a significant number of products (e.g., > 5)
        brands_with_multiple_products = Product.objects.values('brand').annotate(product_count=Count('id')).filter(product_count__gt=5).order_by('-product_count')

        if not brands_with_multiple_products:
            self.stdout.write("No brands found with more than 5 products.")
            return

        self.stdout.write(f"Found {len(brands_with_multiple_products)} brands to analyze...")
        self.stdout.write("-" * 40)

        for brand_data in brands_with_multiple_products:
            brand_name = brand_data['brand']
            product_count = brand_data['product_count']

            if not brand_name:
                continue

            # Get all products for the current brand that have a barcode
            products = Product.objects.filter(brand=brand_name).exclude(barcode__isnull=True).exclude(barcode__exact='')
            barcodes = [p.barcode for p in products]

            if len(barcodes) < 2:
                continue

            # Find the common prefix
            common_prefix = find_longest_common_prefix(barcodes)

            if len(common_prefix) > 3:  # Only show prefixes of a reasonable length
                self.stdout.write(self.style.SUCCESS(f"Brand: {brand_name} ({product_count} products)"))
                self.stdout.write(f"  Potential Prefix: {common_prefix}")
                self.stdout.write(f"  Sample Barcode:   {barcodes[0]}")
                self.stdout.write("-" * 40)

        self.stdout.write(self.style.SUCCESS("--- Analysis Complete ---"))
