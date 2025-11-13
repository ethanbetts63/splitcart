from django.core.management.base import BaseCommand
from products.models import Product, SKU
import json

class Command(BaseCommand):
    help = 'Finds a product in the database by a given Coles SKU.'

    def add_arguments(self, parser):
        parser.add_argument('coles_sku', type=int, help='The Coles SKU to search for.')

    def handle(self, *args, **options):
        coles_sku_to_find = options['coles_sku']

        self.stdout.write(f"--- Starting Step-by-Step SKU Diagnosis (with PKs) ---")

        try:
            # Query the SKU model directly for the given Coles SKU
            sku_obj = SKU.objects.select_related('product', 'product__brand').filter(
                sku=str(coles_sku_to_find),
                company__name__iexact='Coles'
            ).first()

            if sku_obj:
                product = sku_obj.product
                self.stdout.write(self.style.SUCCESS(f"SUCCESS: Found SKU {coles_sku_to_find}."))
                self.stdout.write(f"  - Product PK: {product.pk}")
                self.stdout.write(f"  - Product Name: {product.name}")
                self.stdout.write(f"  - Product Brand: {product.brand.name if product.brand else 'N/A'}")
                self.stdout.write(f"  - Normalized Name: {product.normalized_name_brand_size}")
            else:
                self.stdout.write(self.style.WARNING(f"FAILURE: Could not find any product associated with Coles SKU '{coles_sku_to_find}'."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Diagnosis Complete ---"))
