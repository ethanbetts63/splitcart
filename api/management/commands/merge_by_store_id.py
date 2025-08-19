from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from products.models import Product, Price
from companies.models import Store
from collections import defaultdict

class Command(BaseCommand):
    help = 'Finds and merges duplicate products based on store-specific product IDs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--find',
            action='store_true',
            help='Find products with the same store_product_id within the same store.'
        )
        parser.add_argument(
            '--merge',
            action='store_true',
            help='Merge products with the same store_product_id within the same store.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the merge process without making changes to the database.'
        )

    def handle(self, *args, **options):
        if options['merge']:
            self.merge_by_store_id(dry_run=options['dry_run'])
        elif options['find']:
            self.find_by_store_id()

    def find_by_store_id(self):
        self.stdout.write(self.style.SQL_FIELD('--- Finding duplicates by store_product_id ---'))
        duplicate_groups = self._get_duplicate_store_products()

        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS('No duplicates found.'))
            return

        for group_key, products in duplicate_groups.items():
            store_id, store_product_id = group_key
            try:
                store = Store.objects.get(id=store_id)
                store_name = store.name
            except Store.DoesNotExist:
                store_name = f"Store ID {store_id} (Not Found)"

            self.stdout.write(self.style.WARNING(f"\nDuplicate found for Store: '{store_name}', Store Product ID: '{store_product_id}'"))
            for p in products:
                self.stdout.write(f"  - Product ID: {p.id}, Name: {p.name}, Brand: {p.brand}, Size: {p.size}")

    def merge_by_store_id(self, dry_run):
        if dry_run:
            self.stdout.write(self.style.SQL_FIELD('--- (Dry Run) Merging duplicates by store_product_id ---'))
        else:
            self.stdout.write(self.style.SQL_FIELD('--- Merging duplicates by store_product_id ---'))

        duplicate_groups = self._get_duplicate_store_products()

        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS('No duplicates to merge.'))
            return

        merged_count = 0
        for group_key, products in duplicate_groups.items():
            store_id, store_product_id = group_key
            products.sort(key=lambda p: p.id)
            master_product = products[0]
            duplicate_products = products[1:]

            try:
                store = Store.objects.get(id=store_id)
                store_name = store.name
            except Store.DoesNotExist:
                store_name = f"Store ID {store_id} (Not Found)"

            self.stdout.write(self.style.WARNING(f"\nProcessing Store: '{store_name}', Store Product ID: '{store_product_id}'"))
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
                    self.stdout.write(self.style.ERROR(f"  - An error occurred while merging: {e}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n--- Dry run complete. {len(duplicate_groups)} sets of duplicates identified. ---'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n--- Merge complete. {merged_count} of {len(duplicate_groups)} sets of duplicates merged. ---'))


    def _get_duplicate_store_products(self):
        # This query identifies store_id and store_product_id pairs that are linked to more than one product.
        # We explicitly exclude cases where store_product_id is an empty string.
        duplicate_prices = Price.objects.exclude(store_product_id='') \
                                        .values('store_id', 'store_product_id') \
                                        .annotate(product_count=Count('product', distinct=True)) \
                                        .filter(product_count__gt=1)

        duplicate_groups = defaultdict(list)
        for item in duplicate_prices:
            prices = Price.objects.filter(store_id=item['store_id'], store_product_id=item['store_product_id']).select_related('product')
            products = {price.product for price in prices if price.product}
            if len(products) > 1:
                group_key = (item['store_id'], item['store_product_id'])
                duplicate_groups[group_key] = sorted(list(products), key=lambda p: p.id)

        return duplicate_groups