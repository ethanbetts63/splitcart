from django.core.management.base import BaseCommand
from products.models import Product, Price
from django.db import transaction, IntegrityError
from collections import defaultdict

class Command(BaseCommand):
    help = "Cleans product data, finds, and merges duplicate products."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show what would be changed without modifying the database."
        )
        parser.add_argument(
            '--find-duplicates-only',
            action='store_true',
            help="Only find and report potential duplicate products."
        )
        parser.add_argument(
            '--merge-duplicates',
            action='store_true',
            help="Merge the found duplicate products."
        )

    def _clean_value(self, value):
        """Cleans a string value, converting various null-like strings to None."""
        if value is None:
            return None
        cleaned_val = str(value).strip().lower()
        if cleaned_val in ['none', 'null', '']:
            return None
        return cleaned_val

    def handle(self, *args, **options):
        if options['find_duplicates_only']:
            self.find_duplicates()
        elif options['merge_duplicates']:
            self.merge_duplicates(options['dry_run'])
        else:
            self.clean_data(options['dry_run'])

    def _get_duplicate_groups(self):
        """Finds and returns groups of duplicate products."""
        cleaned_records = defaultdict(list)
        for product in Product.objects.iterator():
            key = (
                self._clean_value(product.name),
                self._clean_value(product.brand),
                self._clean_value(product.size)
            )
            cleaned_records[key].append(product.id)
        return {k: v for k, v in cleaned_records.items() if len(v) > 1}

    def find_duplicates(self):
        self.stdout.write(self.style.SQL_FIELD("--- Finding potential duplicates ---"))
        duplicate_groups = self._get_duplicate_groups()
        
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicate groups found."))
            return

        self.stdout.write(self.style.WARNING(f"Found {len(duplicate_groups)} group(s) of potential duplicates:"))
        for (name, brand, size), ids in duplicate_groups.items():
            self.stdout.write(f"- Group (Name: '{name}', Brand: '{brand}', Size: '{size}')")
            self.stdout.write(f"  Product IDs: {ids}")

    def merge_duplicates(self, dry_run):
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN: MERGE DUPLICATES ---"))
        else:
            self.stdout.write(self.style.SUCCESS("--- LIVE RUN: MERGE DUPLICATES ---"))

        duplicate_groups = self._get_duplicate_groups()
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicates to merge."))
            return

        merged_groups_count = 0
        deleted_products_count = 0

        for (name, brand, size), ids in duplicate_groups.items():
            self.stdout.write(self.style.NOTICE(f"\nProcessing Group: (Name: '{name}', Brand: '{brand}', Size: '{size}')"))
            
            primary_product = Product.objects.get(id=ids[0])
            duplicates_to_merge = Product.objects.filter(id__in=ids[1:])
            
            self.stdout.write(f"  - Keeping Product ID: {primary_product.id}")
            self.stdout.write(f"  - Merging Product IDs: {[d.id for d in duplicates_to_merge]}")

            if not dry_run:
                try:
                    with transaction.atomic():
                        for duplicate in duplicates_to_merge:
                            # 1. Merge simple fields
                            for field in ['barcode', 'image_url', 'url', 'description', 'country_of_origin', 'allergens', 'ingredients']:
                                if not getattr(primary_product, field) and getattr(duplicate, field):
                                    setattr(primary_product, field, getattr(duplicate, field))
                                    self.stdout.write(f"    - Merged field '{field}' from Product ID: {duplicate.id}")
                            
                            # 2. Merge M2M relationships
                            primary_product.category.add(*duplicate.category.all())
                            primary_product.substitute_goods.add(*duplicate.substitute_goods.all())
                            primary_product.size_variants.add(*duplicate.size_variants.all())

                            # 3. Re-assign prices
                            price_count = duplicate.prices.update(product=primary_product)
                            self.stdout.write(f"    - Re-assigned {price_count} price record(s) from Product ID: {duplicate.id}")

                            # 4. Delete duplicate product
                            duplicate.delete()
                            deleted_products_count += 1
                        
                        primary_product.save()
                        merged_groups_count += 1

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"An error occurred while merging group for product '{name}'. Rolling back. Error: {e}"))
            else:
                # Simulate actions for dry run
                for duplicate in duplicates_to_merge:
                    price_count = duplicate.prices.count()
                    self.stdout.write(f"  [DRY RUN] Would re-assign {price_count} price record(s) from Product ID: {duplicate.id}")
                    self.stdout.write(f"  [DRY RUN] Would merge fields and relationships from Product ID: {duplicate.id}")
                    self.stdout.write(f"  [DRY RUN] Would delete Product ID: {duplicate.id}")
                merged_groups_count += 1
                deleted_products_count += len(ids) - 1


        self.stdout.write(self.style.SUCCESS("--- Merge Summary ---"))
        self.stdout.write(f"Total groups processed: {merged_groups_count}")
        self.stdout.write(f"Total products deleted: {deleted_products_count}")
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run. No changes were made to the database."))

    def clean_data(self, dry_run):
        # This method remains unchanged.
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: CLEAN DATA ---"))
        else:
            self.stdout.write(self.style.SUCCESS("--- LIVE RUN MODE: CLEAN DATA ---"))

        changed_count = 0
        for product in Product.objects.iterator():
            original_tuple = (product.name, product.brand, product.size)
            
            product.name = self._clean_value(product.name)
            product.brand = self._clean_value(product.brand)
            product.size = self._clean_value(product.size)
            
            if (product.name, product.brand, product.size) != original_tuple:
                changed_count += 1
                if dry_run:
                    self.stdout.write(f"Product ID: {product.id} would be changed.")
                else:
                    try:
                        with transaction.atomic():
                            product.save()
                    except IntegrityError:
                        self.stderr.write(self.style.ERROR(f"Failed to update Product ID: {product.id}. A duplicate likely exists."))

        self.stdout.write(f"\nTotal products that would be/were changed: {changed_count}")
