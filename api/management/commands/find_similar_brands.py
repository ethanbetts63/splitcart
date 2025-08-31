from django.core.management.base import BaseCommand
from products.models import Product
from api.utils.normalizer import ProductNormalizer
import os
import json

class Command(BaseCommand):
    help = 'Finds brand names similar to Coles or Woolworths based on naming conventions.'

    def handle(self, *args, **options):
        output_filename = 'similar_brands_log.txt'
        self.stdout.write("Starting brand similarity analysis...")

        unique_brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
        self.stdout.write(f"Found {len(unique_brands)} unique brand names in the database.")

        companies_to_check = ["coles", "woolworths"]

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write("--- Brand Similarity Analysis ---\n\n")
                for brand_name in unique_brands:
                    if not brand_name: # Skip empty brand names
                        continue

                    contains_company_name = False
                    for company in companies_to_check:
                        if company in brand_name.lower():
                            contains_company_name = True
                            break

                    if contains_company_name: # Only output if it contains a company name keyword
                        f.write(f"Brand: {brand_name}\n\n")
            self.stdout.write(self.style.SUCCESS(f"Successfully wrote brand analysis to {output_filename}"))
        except IOError as e:
            self.stderr.write(self.style.ERROR(f"Failed to write to file: {e}"))

        self.stdout.write(self.style.SUCCESS("\nBrand similarity analysis complete."))
