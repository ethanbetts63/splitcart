from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Cleans the brand_name_company_pairs field on all Product objects.'

    def handle(self, *args, **options):
        self.stdout.write("Starting cleanup of brand_name_company_pairs...")
        
        products_to_update = []
        products_iterator = Product.objects.iterator(chunk_size=2000)
        total_products = Product.objects.count()
        processed_count = 0
        updated_count = 0

        for product in products_iterator:
            processed_count += 1
            if processed_count % 1000 == 0:
                self.stdout.write(f"  - Processed {processed_count}/{total_products} products...")

            original_pairs = product.brand_name_company_pairs
            if not original_pairs:
                continue

            cleaned_pairs = []
            made_change = False
            for pair in original_pairs:
                # Ensure the pair is a list of length 2 before unpacking
                if isinstance(pair, list) and len(pair) == 2:
                    raw_brand_name, company_name = pair
                    # Check if the brand name is a string and all lowercase
                    # It must not be equal to its uppercase version to exclude purely numeric/symbolic strings
                    if isinstance(raw_brand_name, str) and raw_brand_name.islower() and raw_brand_name.upper() != raw_brand_name.lower():
                        cleaned_pairs.append([None, company_name])
                        made_change = True
                    else:
                        cleaned_pairs.append(pair)
                else:
                    # If the pair format is incorrect, append it as is to avoid data loss
                    cleaned_pairs.append(pair)
            
            if made_change:
                product.brand_name_company_pairs = cleaned_pairs
                products_to_update.append(product)
                updated_count += 1

            # Update in batches of 500 to be memory efficient
            if len(products_to_update) >= 500:
                Product.objects.bulk_update(products_to_update, ['brand_name_company_pairs'])
                self.stdout.write(f"    ... updated a batch of {len(products_to_update)} products.")
                products_to_update = []

        # Update any remaining products
        if products_to_update:
            Product.objects.bulk_update(products_to_update, ['brand_name_company_pairs'])
            self.stdout.write(f"    ... updated a final batch of {len(products_to_update)} products.")

        self.stdout.write(self.style.SUCCESS(f"Cleanup complete. Processed {processed_count} products and updated {updated_count} products."))
