from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Removes entries from brand_name_company_pairs where the brand name is all lowercase.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting cleanup of brand_name_company_pairs ---"))

        products_to_update = []
        
        # We only care about products that have pairs to check
        products_with_pairs = Product.objects.exclude(brand_name_company_pairs__isnull=True).exclude(brand_name_company_pairs__exact=[])
        
        total_to_check = products_with_pairs.count()
        self.stdout.write(f"Found {total_to_check} products with brand/company pairs to check...")

        # Use iterator() for memory efficiency
        for i, product in enumerate(products_with_pairs.iterator()):
            if (i + 1) % 2000 == 0:
                self.stdout.write(f"  - Checked {i + 1}/{total_to_check} products...")

            # A sanity check, though the query should prevent this
            if not isinstance(product.brand_name_company_pairs, list):
                continue

            original_pairs = product.brand_name_company_pairs
            
            # Keep a pair if the brand name is NOT (all lowercase AND all alphabetic)
            # This correctly handles brands like "a2" or "7-eleven" while removing "woolworths"
            cleaned_pairs = [
                pair for pair in original_pairs 
                if not (len(pair) == 2 and isinstance(pair[0], str) and pair[0].islower() and pair[0].isalpha())
            ]

            # If the list of pairs has changed, stage the product for update
            if len(original_pairs) != len(cleaned_pairs):
                product.brand_name_company_pairs = cleaned_pairs
                products_to_update.append(product)
        
        self.stdout.write(f"Finished checking products. Found {len(products_to_update)} products requiring updates.")

        if not products_to_update:
            self.stdout.write(self.style.SUCCESS("No products needed updating. Data is clean."))
            return

        self.stdout.write(f"Starting bulk update for {len(products_to_update)} products...")

        # Update the database in batches
        Product.objects.bulk_update(products_to_update, ['brand_name_company_pairs'], batch_size=500)

        self.stdout.write(self.style.SUCCESS(f"--- Successfully updated {len(products_to_update)} products. ---"))
