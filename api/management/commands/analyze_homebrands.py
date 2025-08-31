from django.core.management.base import BaseCommand
from products.models import Product
import json

class Command(BaseCommand):
    help = 'Analyzes homebrand product distribution for specified companies.'

    def handle(self, *args, **options):
        self.stdout.write("Starting homebrand analysis...")

        companies_to_analyze = ["Coles", "Woolworths"]

        for company_name in companies_to_analyze:
            self.stdout.write(f"\n--- Analyzing products for brand: {company_name} ---")
            
            # Total products in the entire database (for percentage denominator)
            total_products_in_db = Product.objects.count()
            
            # Homebrand products (numerator for percentage)
            homebrand_products_count = Product.objects.filter(brand__iexact=company_name).count()

            percentage_homebrand = 0.0
            if total_products_in_db > 0:
                percentage_homebrand = (homebrand_products_count / total_products_in_db) * 100

            self.stdout.write(f"Total products in DB: {total_products_in_db}")
            self.stdout.write(f"Homebrand products ('{company_name}' brand): {homebrand_products_count}")
            self.stdout.write(f"Percentage homebrand: {percentage_homebrand:.2f}%")

            # Save product details to a file
            output_filename = f"{company_name.lower()}_products.txt"
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Products with brand '{company_name}':\n\n")
                    for product in Product.objects.filter(brand__iexact=company_name).order_by('name'):
                        f.write(f"--------------------------------------------------\n")
                        f.write(f"Product ID: {product.id}\n")
                        f.write(f"Name: {product.name}\n")
                        f.write(f"Brand: {product.brand}\n")
                        f.write(f"Barcode: {product.barcode}\n")
                        f.write(f"Normalized String: {product.normalized_name_brand_size}\n")
                        f.write(f"--------------------------------------------------\n\n")
                self.stdout.write(f"Details saved to {output_filename}")
            except IOError as e:
                self.stderr.write(self.style.ERROR(f"Failed to write to {output_filename}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nHomebrand analysis complete."))
