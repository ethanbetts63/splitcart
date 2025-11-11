from django.core.management.base import BaseCommand
from products.models import Product
import json

class Command(BaseCommand):
    help = 'Finds a product in the database by a given Coles SKU.'

    def add_arguments(self, parser):
        parser.add_argument('coles_sku', type=int, help='The Coles SKU to search for.')

    def handle(self, *args, **options):
        coles_sku_to_find = options['coles_sku'] # We will use this at the end

        self.stdout.write(f"--- Starting Step-by-Step SKU Diagnosis ---")

        try:
            # Step 1: Get all products
            all_products = list(Product.objects.all())
            self.stdout.write(f"Step 1: Fetched {len(all_products)} total products from the database.")

            # Step 2: Cache `company_skus`
            company_skus_cache = [p.company_skus for p in all_products if p.company_skus]
            self.stdout.write(f"Step 2: Cached {len(company_skus_cache)} non-empty 'company_skus' fields.")

            # Step 3: Find products with a 'coles' key
            coles_sku_products = []
            for sku_dict in company_skus_cache:
                if 'coles' in sku_dict:
                    coles_sku_products.append(sku_dict)
            self.stdout.write(f"Step 3: Found {len(coles_sku_products)} products with a 'coles' key.")

            # Step 4: Print the final list
            self.stdout.write(self.style.HTTP_INFO("\n--- Raw 'company_skus' data for all products with a 'coles' key ---"))
            if coles_sku_products:
                self.stdout.write(json.dumps(coles_sku_products, indent=2))
            else:
                self.stdout.write("No 'company_skus' dictionaries with a 'coles' key were found.")
            
            # Final check for the specific SKU within the found data
            self.stdout.write(self.style.HTTP_INFO(f"\n--- Final check for specific SKU: {coles_sku_to_find} ---"))
            product_found = False
            for sku_dict in coles_sku_products:
                coles_data = sku_dict.get('coles')
                if not coles_data:
                    continue
                
                # Handle both list and single value
                if not isinstance(coles_data, list):
                    coles_data = [coles_data]
                
                if coles_sku_to_find in coles_data or str(coles_sku_to_find) in coles_data:
                    self.stdout.write(self.style.SUCCESS(f"SUCCESS: Found SKU {coles_sku_to_find} in dictionary: {json.dumps(sku_dict)}"))
                    product_found = True
            
            if not product_found:
                self.stdout.write(self.style.WARNING(f"FAILURE: Could not find SKU {coles_sku_to_find} in any of the {len(coles_sku_products)} products that have a 'coles' key."))


        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Diagnosis Complete ---"))
