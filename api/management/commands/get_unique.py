from django.core.management.base import BaseCommand
from products.models.product import Product
from api.utils.product_normalizer import ProductNormalizer
import os

class Command(BaseCommand):
    help = 'Gets unique brands or all normalized strings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--brands',
            action='store_true',
            help='Get unique brand names.'
        )
        parser.add_argument(
            '--normalized',
            action='store_true',
            help='Get all normalized strings.'
        )
        parser.add_argument(
            '--barcodes',
            action='store_true',
            help='Get unique barcodes.'
        )

    def handle(self, *args, **options):
        if options['brands']:
            self.get_unique_brands()
        elif options['normalized']:
            self.get_normalized_name_brand_size_strings()
        elif options['barcodes']:
            self.get_unique_barcodes()
        else:
            self.stdout.write(self.style.ERROR("Please specify either --brands, --normalized, or --barcodes."))

    def get_unique_barcodes(self):
        self.stdout.write("Getting unique barcodes...")
        # Using .values_list() and .distinct() is efficient
        barcodes = Product.objects.values_list('barcode', flat=True).distinct()

        output_file = os.path.join('unique_barcodes.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for barcode in barcodes:
                if barcode: # Filter out None or empty strings
                    f.write(f"{barcode}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote unique barcodes to {output_file}"))

    def get_unique_brands(self):
        self.stdout.write("Getting unique brands with example products...")
        
        products = Product.objects.filter(brand__isnull=False).exclude(brand='').order_by('brand')

        unique_brands_with_examples = {}

        for product in products:
            product_data = {'brand': product.brand.name if product.brand else None, 'name': product.name}
            normalizer = ProductNormalizer(product_data)
            normalized_brand = normalizer.cleaned_brand

            if normalized_brand and normalized_brand not in unique_brands_with_examples:
                unique_brands_with_examples[normalized_brand] = (product.name, product.sizes)
        
        unique_sorted_brands = sorted(unique_brands_with_examples.keys())

        output_file = os.path.join('unique_brands.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for brand in unique_sorted_brands:
                raw_name, sizes_list = unique_brands_with_examples[brand]
                sizes_str = ", ".join(map(str, sizes_list)) if sizes_list else "N/A"
                f.write(f"{brand} ({raw_name}, {sizes_str})\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote unique brands with examples to {output_file}"))

    def get_normalized_name_brand_size_strings(self):
        self.stdout.write("Getting all normalized strings...")
        normalized_strings = Product.objects.values_list('normalized_name_brand_size', flat=True)
        
        output_file = os.path.join('normalized_strings.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for s in normalized_strings:
                if s:
                    f.write(f"{s}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote normalized strings to {output_file}"))