from django.core.management.base import BaseCommand
from products.models.product import Product
import os

class Command(BaseCommand):
    help = 'Gets all unique brand names and writes them to a file.'

    def handle(self, *args, **options):
        # Get unique brand names, filter out null/empty, and order them
        unique_brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
        unique_brands = [brand for brand in unique_brands if brand]

        # Define the output file path
        output_file = os.path.join('unique_brands.txt')

        # Write the unique brands to the file
        with open(output_file, 'w') as f:
            for brand in unique_brands:
                f.write(f"{brand}\n")

        self.stdout.write(self.style.SUCCESS(f"Successfully wrote unique brands to {output_file}"))
