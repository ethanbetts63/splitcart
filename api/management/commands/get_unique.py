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
        self.stdout.write("Getting unique brands...")
        # Get all brand names
        all_brands = Product.objects.values_list('brand', flat=True)

        # Process the brands: strip, lowercase, and get unique values
        processed_brands = {brand.strip().lower() for brand in all_brands if brand}

        # Sort the unique brands alphabetically
        unique_sorted_brands = sorted(list(processed_brands))

        # Define the output file path
        output_file = os.path.join('unique_brands.txt')

        # Write the unique brands to the file
        with open(output_file, 'w', encoding='utf-8') as f:
            for brand in unique_sorted_brands:
                f.write(f"{brand}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote unique brands to {output_file}"))

    def get_normalized_strings(self):
        self.stdout.write("Getting all normalized strings...")
        normalized_strings = Product.objects.values_list('normalized_name_brand_size', flat=True)
        
        output_file = os.path.join('normalized_strings.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
            for s in normalized_strings:
                if s:
                    f.write(f"{s}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote normalized strings to {output_file}"))