import re
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Price

def normalize_name(name):
    """
    Normalizes a product name by lowercasing, removing punctuation,
    and sorting the words alphabetically.
    """
    if not name:
        return ''
    name = re.sub(r'[^\w\s]', '', name).lower()
    tokens = sorted(name.split())
    return ' '.join(tokens)

class Command(BaseCommand):
    help = 'Merges fuzzy duplicate products based on normalized name, brand, and size.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--merge',
            action='store_true',
            default=True,
            help='Merge potential fuzzy duplicates that have the same name, brand, and size.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the merge process without making changes to the database.'
        )

    def handle(self, *args, **options):
        if options['merge']:
            self.merge_duplicates(dry_run=options['dry_run'])

    def merge_duplicates(self, dry_run):
        if dry_run:
            self.stdout.write(self.style.SQL_FIELD('--- (Dry Run) Merging duplicates by normalized name, brand, and size ---'))
        else:
            self.stdout.write(self.style.SQL_FIELD('--- Merging duplicates by normalized name, brand, and size ---'))

        # Group products by normalized name, brand, and size
        product_groups = defaultdict(list)
        for product in Product.objects.all():
            normalized = normalize_name(product.name)
            brand = product.brand.lower().strip() if product.brand else ''
            size = product.size.lower().strip() if product.size else ''
            product_groups[(normalized, brand, size)].append(product)

        # Filter for groups with more than one product
        duplicate_groups = {key: products for key, products in product_groups.items() if len(products) > 1}

        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS('No duplicates to merge found with this method.'))
            return

        merged_count = 0
        for (normalized_name, brand, size), products in duplicate_groups.items():
            products.sort(key=lambda p: p.id)
            master_product = products[0]
            products_to_merge = products[1:]

            self.stdout.write(self.style.WARNING(f"\nProcessing Group: Name='{normalized_name}', Brand='{brand}', Size='{size}'"))
            self.stdout.write(f"  - Master product (keeping): ID {master_product.id} ('{master_product.name}')")

            for p in products_to_merge:
                price_count = Price.objects.filter(product=p).count()
                self.stdout.write(f"    - Merging product: ID {p.id} ('{p.name}') - {price_count} price records to move.")

            if not dry_run:
                try:
                    with transaction.atomic():
                        for p in products_to_merge:
                            Price.objects.filter(product=p).update(product=master_product)
                            p.delete()
                        self.stdout.write(self.style.SUCCESS(f"  - Successfully merged {len(products_to_merge)} duplicates into product {master_product.id}."))
                        merged_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  - An error occurred while merging: {e}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n--- Dry run complete. {len(duplicate_groups)} sets of duplicates identified. ---'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n--- Merge complete. {merged_count} of {len(duplicate_groups)} sets of duplicates merged. ---'))
