from django.core.management.base import BaseCommand
from products.models.product import Product
import os

class Command(BaseCommand):
    help = 'Gets all unique brand names and writes them to a file.'

    def handle(self, *args, **options):
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
