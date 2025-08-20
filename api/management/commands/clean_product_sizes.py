import re
from django.core.management.base import BaseCommand
from products.models import Product
from django.db.models import Q

class Command(BaseCommand):
    help = 'Cleans and standardizes the `size` field for all products.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the script without saving any changes to the database. It will print a summary of the changes that would be made.'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING("--- Running in DRY-RUN mode. No changes will be saved. ---"))
        else:
            self.stdout.write(self.style.SUCCESS("--- Starting product size cleaning process ---"))

        # --- Step 1: Handle products with empty string sizes ---
        empty_string_products = Product.objects.filter(size__exact='')
        empty_count = empty_string_products.count()
        if empty_count > 0:
            self.stdout.write(f"Found {empty_count} products with empty string size to be set to Null.")
            if not dry_run:
                empty_string_products.update(size=None)
        else:
            self.stdout.write("No products with empty string size found.")

        # --- Step 2: Apply cleaning rules to all other products ---
        products_to_check = Product.objects.filter(Q(size__isnull=False) & ~Q(size__exact=''))
        total_products = products_to_check.count()
        self.stdout.write(f"Found {total_products} products with size information to check for cleaning.")

        products_to_update = []
        change_log = [] # To store details for dry run
        
        rules = {
            r'approx\.': '',
            r'\s*gram\s*': 'g',
            r'\s*litre\s*': 'lt',
            r'\s*pack\s*': 'pk',
            r'\s*kilo\s*': 'kg',
            r'eachunit': 'each',
            r'(\d)\s+([a-zA-Z])': r'\1\2',
        }

        for product in products_to_check.iterator(chunk_size=2000):
            original_size = product.size
            new_size = original_size.lower().strip()

            for pattern, replacement in rules.items():
                new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)

            new_size = new_size.strip()

            if new_size != original_size:
                if dry_run:
                    if len(change_log) < 20: # Log first 20 changes for review
                        change_log.append((product.id, original_size, new_size))
                
                product.size = new_size
                name_str = str(product.name or '').strip().lower()
                brand_str = str(product.brand or '').strip().lower()
                size_str = str(product.size or '').strip().lower()
                product.normalized_name_brand_size = f"{name_str}-{brand_str}-{size_str}"
                products_to_update.append(product)

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n--- DRY-RUN: Sample of changes that would be made ---"))
            if not change_log and empty_count == 0:
                self.stdout.write("No changes would be made.")
            else:
                for pid, old, new in change_log:
                    self.stdout.write(f"  Product ID {pid}: '{old}' -> '{new}'")
                if len(products_to_update) > len(change_log):
                    self.stdout.write(f"  ...and {len(products_to_update) - len(change_log)} more products.")
        else:
            if products_to_update:
                self.stdout.write(f"Updating {len(products_to_update)} products with cleaned sizes...")
                Product.objects.bulk_update(products_to_update, ['size', 'normalized_name_brand_size'], batch_size=999)
                self.stdout.write(self.style.SUCCESS("Bulk update complete."))
            else:
                self.stdout.write(self.style.WARNING("No products needed size cleaning based on the defined rules."))
        
        total_affected = len(products_to_update) + empty_count
        final_message = f"--- Cleaning process complete. Total products affected: {total_affected} ---"
        if dry_run:
            final_message = f"--- DRY-RUN complete. Total products that would be affected: {total_affected} ---"
        
        self.stdout.write(self.style.SUCCESS(final_message))
