from django.core.management.base import BaseCommand
from products.models.product import Product
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

    def handle(self, *args, **options):
        if options['brands']:
            self.get_unique_brands()
        elif options['normalized']:
            self.get_normalized_strings()
        else:
            self.stdout.write(self.style.ERROR("Please specify either --brands or --normalized."))

    def get_unique_brands(self):
        self.stdout.write("Getting unique brands with example products...")
        
        # Get all products that have a brand, ordered by brand
        products = Product.objects.filter(brand__isnull=False).exclude(brand='').order_by('brand')

        # Use a dictionary to store unique brands and their first encountered example product
        unique_brands_with_examples = {} # {normalized_brand: (raw_name, sizes_list)}

        for product in products:
            normalized_brand = product.brand.strip().lower()
            if normalized_brand not in unique_brands_with_examples:
                # Store the raw name and the sizes list
                unique_brands_with_examples[normalized_brand] = (product.name, product.sizes)
        
        # Sort the unique brands alphabetically
        unique_sorted_brands = sorted(unique_brands_with_examples.keys())

        output_file = os.path.join('unique_brands.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for brand in unique_sorted_brands:
                raw_name, sizes_list = unique_brands_with_examples[brand]
                # Format the sizes list into a readable string
                sizes_str = ", ".join(sizes_list) if sizes_list else "N/A"
                f.write(f"{brand} ({raw_name}, {sizes_str})\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote unique brands with examples to {output_file}"))

    def get_normalized_strings(self):
        self.stdout.write("Getting all normalized strings...")
        normalized_strings = Product.objects.values_list('normalized_name_brand_size', flat=True)
        
        output_file = os.path.join('normalized_strings.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for s in normalized_strings:
                if s:
                    f.write(f"{s}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote normalized strings to {output_file}"))