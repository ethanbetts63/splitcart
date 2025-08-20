from django.core.management.base import BaseCommand
from products.models import Product
from django.db import transaction, IntegrityError
from collections import defaultdict

class Command(BaseCommand):
    help = "Cleans data in the Product table and finds potential duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show what would be changed without modifying the database."
        )
        parser.add_argument(
            '--find-duplicates-only',
            action='store_true',
            help="Find and report products that will become duplicates after cleaning."
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
        else:
            self.clean_data(options['dry_run'])

    def find_duplicates(self):
        self.stdout.write(self.style.SQL_FIELD("--- Finding potential duplicates ---"))
        cleaned_records = defaultdict(list)
        
        for product in Product.objects.iterator():
            cleaned_name = self._clean_value(product.name)
            cleaned_brand = self._clean_value(product.brand)
            cleaned_size = self._clean_value(product.size)
            
            # Use a tuple of cleaned values as the key
            key = (cleaned_name, cleaned_brand, cleaned_size)
            cleaned_records[key].append(product.id)
            
        # Filter for groups with more than one product
        duplicate_groups = {k: v for k, v in cleaned_records.items() if len(v) > 1}
        
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicate groups found after cleaning."))
            return

        self.stdout.write(self.style.WARNING(f"Found {len(duplicate_groups)} group(s) of potential duplicates:"))
        for (name, brand, size), ids in duplicate_groups.items():
            self.stdout.write(f"- Group (Name: '{name}', Brand: '{brand}', Size: '{size}')")
            self.stdout.write(f"  Product IDs: {ids}")

    def clean_data(self, dry_run):
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE ---"))
        else:
            self.stdout.write(self.style.SUCCESS("--- LIVE RUN MODE ---"))

        changed_count = 0
        success_count = 0
        failure_count = 0
        total_scanned = 0

        for product in Product.objects.iterator():
            total_scanned += 1
            original_tuple = (product.name, product.brand, product.size)
            
            cleaned_name = self._clean_value(product.name)
            cleaned_brand = self._clean_value(product.brand)
            cleaned_size = self._clean_value(product.size)
            
            if (cleaned_name != original_tuple[0] or
                cleaned_brand != original_tuple[1] or
                cleaned_size != original_tuple[2]):
                
                changed_count += 1
                product.name = cleaned_name
                product.brand = cleaned_brand
                product.size = cleaned_size

                if dry_run:
                    self.stdout.write(f"Product ID: {product.id} would be changed:")
                    if cleaned_name != original_tuple[0]: self.stdout.write(f"  Name:  '{original_tuple[0]}' -> '{cleaned_name}'")
                    if cleaned_brand != original_tuple[1]: self.stdout.write(f"  Brand: '{original_tuple[1]}' -> '{cleaned_brand}'")
                    if cleaned_size != original_tuple[2]: self.stdout.write(f"  Size:  '{original_tuple[2]}' -> '{cleaned_size}'")
                else:
                    try:
                        # Use a transaction for each save to handle errors gracefully
                        with transaction.atomic():
                            product.save()
                        success_count += 1
                    except IntegrityError:
                        self.stderr.write(self.style.ERROR(f"Failed to update Product ID: {product.id}. A duplicate likely exists."))
                        self.stderr.write(self.style.ERROR(f"  Attempted to save: (Name: '{cleaned_name}', Brand: '{cleaned_brand}', Size: '{cleaned_size}')"))
                        failure_count += 1

        self.stdout.write(self.style.SUCCESS("\n--- Summary ---"))
        self.stdout.write(f"Total products scanned: {total_scanned}")
        self.stdout.write(f"Products requiring changes: {changed_count}")
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated: {success_count}"))
            self.stdout.write(self.style.ERROR(f"Failed to update (due to conflicts): {failure_count}"))
        self.stdout.write(self.style.WARNING("Run complete."))