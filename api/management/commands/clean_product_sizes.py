import re
import random
from django.core.management.base import BaseCommand
from products.models import Product
from django.db.models import Q
from django.db import IntegrityError, DatabaseError
from api.utils.database_updating_utils.merging import merge_duplicate_products

class Command(BaseCommand):
    help = 'Cleans and standardizes the `size` field for all products and merges duplicates.'

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
            self.stdout.write(self.style.WARNING("--- Starting product size cleaning process. This may be very slow due to individual product lookups and duplicate checks. ---"))

        # --- Step 1: Handle products with empty string sizes ---
        empty_string_products = Product.objects.filter(size__exact='')
        empty_count = empty_string_products.count()
        if empty_count > 0:
            self.stdout.write(f"Found {empty_count} products with empty string size to be set to Null.")
            if not dry_run:
                empty_string_products.update(size=None)
        else:
            self.stdout.write("No products with empty string size found.")

        # --- Step 2: Get a static list of IDs to process ---
        products_to_check_qs = Product.objects.filter(Q(size__isnull=False) & ~Q(size__exact=''))
        product_ids = list(products_to_check_qs.values_list('pk', flat=True))
        total_products = len(product_ids)
        self.stdout.write(f"Found {total_products} products with size information to check for cleaning.")

        change_log = []
        update_counter = 0
        merge_counter = 0
        skip_counter = 0
        next_log_point = random.randint(60, 100) if dry_run else 0

        # --- Cleaning Rules ---
        normalization_rules = {r'approx\.': '', r'(\d)\s+([a-zA-Z])': r'\1\2'}
        unit_rules = {r'\s*gram\s*': 'g', r'\s*litre\s*': 'lt', r'\s*pack\s*': 'pk', r'\s*kilo\s*': 'kg', r'\s*case\s*': 'pk', r'eachunit': 'each'}
        quantity_rules = {r'1\s*each|1\.1\s*each': 'each'}

        for i, product_id in enumerate(product_ids):
            if i % 1000 == 0:
                self.stdout.write(f"Processing product {i} of {total_products}...")
            
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                skip_counter += 1
                continue # Product was deleted by a previous merge, skip.

            original_size = product.size
            new_size = original_size.lower().strip()

            for pattern, replacement in normalization_rules.items(): new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)
            for pattern, replacement in unit_rules.items(): new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)
            for pattern, replacement in quantity_rules.items(): new_size = re.sub(pattern, replacement, new_size, flags=re.IGNORECASE)

            l_match = re.match(r'^(\d+\.?\d*)\s*l$', new_size)
            if l_match: new_size = f'{int(float(l_match.group(1)) * 1000)}ml'
            kg_match = re.match(r'^(\d+\.?\d*)\s*kg$', new_size)
            if kg_match: new_size = f'{int(float(kg_match.group(1)) * 1000)}g'

            new_size = new_size.strip()

            if new_size != original_size:
                product.size = new_size

                if dry_run:
                    update_counter += 1
                    if update_counter >= next_log_point:
                        change_log.append((product.id, original_size, new_size))
                        next_log_point += random.randint(60, 100)
                    try:
                        temp_key = f"{product._clean_value(product.name)}_{product._clean_value(product.brand)}_{product._clean_value(new_size)}"
                        conflicting_product = Product.objects.exclude(pk=product.pk).get(normalized_name_brand_size=temp_key)
                        change_log.append(f"  - Product {product.id} would conflict with {conflicting_product.id}. MERGE would occur.")
                        merge_counter += 1
                    except Product.DoesNotExist: pass
                    except Product.MultipleObjectsReturned: change_log.append(f"  - WARNING: Product {product.id} would conflict with MULTIPLE existing products.")
                else:
                    try:
                        product.save(update_fields=['size', 'normalized_name_brand_size'])
                        update_counter += 1
                    except IntegrityError:
                        try:
                            conflicting_product = Product.objects.exclude(pk=product.pk).get(normalized_name_brand_size=product.normalized_name_brand_size)
                            self.stdout.write(self.style.WARNING(f"Conflict found. Merging product {conflicting_product.id} into {product.id}."))
                            merge_log = merge_duplicate_products(product_to_keep=product, product_to_delete=conflicting_product, dry_run=False)
                            merge_counter += 1
                            for msg in merge_log: self.stdout.write(self.style.SUCCESS(f"  - {msg}"))
                        except Product.DoesNotExist: self.stdout.write(self.style.ERROR(f"IntegrityError for product {product.id} but no conflicting product found."))
                        except Product.MultipleObjectsReturned: self.stdout.write(self.style.WARNING(f"Product {product.id} conflicts with MULTIPLE existing products. Manual intervention required."))
                    except DatabaseError as e:
                        self.stdout.write(self.style.ERROR(f"DatabaseError for product {product.id}: {e}. This can happen if the product was deleted mid-process. Skipping."))
                        skip_counter += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n--- DRY-RUN: Sample of changes that would be made ---"))
            for item in change_log: self.stdout.write(f"  {item}")
            self.stdout.write(f"\n--- DRY-RUN complete. ---")
            self.stdout.write(f"- Would update {update_counter} products.")
            self.stdout.write(f"- Would merge {merge_counter} duplicates.")
            self.stdout.write(f"- Would set {empty_count} empty sizes to Null.")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n--- Cleaning process complete. ---"))
            self.stdout.write(f"- Updated {update_counter} products.")
            self.stdout.write(f"- Merged {merge_counter} duplicates.")
            self.stdout.write(f"- Skipped {skip_counter} products (deleted mid-process).")
            self.stdout.write(f"- Set {empty_count} empty sizes to Null.")
