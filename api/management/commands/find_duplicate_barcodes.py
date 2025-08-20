from django.core.management.base import BaseCommand
from products.models import Product
from collections import defaultdict

class Command(BaseCommand):
    help = "Finds products that have duplicate barcodes, including those with empty or null barcodes."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SQL_FIELD("--- Finding duplicate barcodes ---"))
        
        barcode_map = defaultdict(list)
        # Iterate through all products, including those with null or empty barcodes
        for product in Product.objects.iterator():
            # Standardize None to empty string for consistent grouping
            barcode_value = product.barcode if product.barcode is not None else ''
            barcode_map[barcode_value].append(product.id)
            
        # Filter for barcodes associated with more than one product
        # Exclude the empty string if it's the only 'duplicate' and it's due to multiple nulls/blanks
        duplicate_groups = {k: v for k, v in barcode_map.items() if len(v) > 1}
        
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS("No duplicate barcodes found."))
            return

        self.stdout.write(self.style.WARNING(f"Found {len(duplicate_groups)} barcode(s) shared by multiple products:"))
        for barcode, ids in duplicate_groups.items():
            # Display empty string as '<EMPTY/NULL>' for clarity
            display_barcode = f"'{barcode}'" if barcode != '' else '<EMPTY/NULL>'
            self.stdout.write(f"- Barcode: {display_barcode}")
            self.stdout.write(f"  Product IDs: {ids}")