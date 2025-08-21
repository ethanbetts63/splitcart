from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Price
from collections import defaultdict

class Command(BaseCommand):
    help = 'Finds and merges potential duplicate products in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--barcode',
            action='store_true',
            help='Find products with duplicate barcodes.'
        )
        parser.add_argument(
            '--merge-by-barcode',
            action='store_true',
            help='Merge products with duplicate barcodes.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the merge process without making changes to the database.'
        )

    def handle(self, *args, **options):
        if options['merge_by_barcode']:
            self.merge_by_barcode(dry_run=options['dry_run'])
        elif options['barcode']:
            self.find_by_barcode()

    def find_by_barcode(self):
        self.stdout.write(self.style.SQL_FIELD('--- Finding products with duplicate barcodes ---'))
        
        barcodes = self._get_duplicate_barcodes()
        
        if not barcodes:
            self.stdout.write(self.style.SUCCESS('No duplicate barcodes found.'))
            return

        self.stdout.write(f'Found {len(barcodes)} sets of products with duplicate barcodes.')
        for barcode, products in barcodes.items():
            self.stdout.write(self.style.WARNING(f"Duplicate barcode found: {barcode}"))
            for p in products:
                self.stdout.write(f"  - Product ID: {p.id}, Name: {p.name}, Brand: {p.brand}, Size: {p.sizes}")

    def merge_by_barcode(self, dry_run):
        if dry_run:
            self.stdout.write(self.style.SQL_FIELD('--- (Dry Run) Merging products with duplicate barcodes ---'))
        else:
            self.stdout.write(self.style.SQL_FIELD('--- Merging products with duplicate barcodes ---'))

        barcodes = self._get_duplicate_barcodes()

        if not barcodes:
            self.stdout.write(self.style.SUCCESS('No duplicate barcodes to merge.'))
            return

        merged_count = 0
        for barcode, products in barcodes.items():
            products.sort(key=lambda p: p.id)
            master_product = products[0]
            duplicate_products = products[1:]

            self.stdout.write(self.style.WARNING(f"\nProcessing barcode: {barcode}"))
            self.stdout.write(f"  - Master product (keeping): ID {master_product.id} ({master_product.name})")

            for p in duplicate_products:
                price_count = Price.objects.filter(product=p).count()
                self.stdout.write(f"    - Merging product: ID {p.id} ({p.name}) - {price_count} price records to move.")

            if not dry_run:
                try:
                    with transaction.atomic():
                        for p in duplicate_products:
                            Price.objects.filter(product=p).update(product=master_product)
                            p.delete()
                        self.stdout.write(self.style.SUCCESS(f"  - Successfully merged {len(duplicate_products)} duplicates into product {master_product.id}."))
                        merged_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  - An error occurred while merging duplicates for barcode {barcode}: {e}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n--- Dry run complete. {len(barcodes)} sets of duplicates identified. ---'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n--- Merge complete. {merged_count} of {len(barcodes)} sets of duplicates merged. ---'))

    def _get_duplicate_barcodes(self):
        products_with_barcodes = Product.objects.filter(barcode__isnull=False).exclude(barcode='')
        
        barcodes = defaultdict(list)
        for product in products_with_barcodes:
            barcodes[product.barcode].append(product)
            
        return {barcode: products for barcode, products in barcodes.items() if len(products) > 1}