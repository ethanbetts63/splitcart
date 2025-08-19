import re
from collections import defaultdict
from django.core.management.base import BaseCommand
from products.models import Product

def normalize_name(name):
    """
    Normalizes a product name by lowercasing, removing punctuation,
    and sorting the words alphabetically.
    """
    if not name:
        return ''
    # Remove punctuation and convert to lowercase
    name = re.sub(r'[^\w\s]', '', name).lower()
    # Split into words, sort them, and join back together
    tokens = sorted(name.split())
    return ' '.join(tokens)

class Command(BaseCommand):
    help = 'Finds potential fuzzy duplicates based on normalized product names and brands.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--find',
            action='store_true',
            default=True,
            help='Find and display potential fuzzy duplicates.'
        )
        parser.add_argument(
            '--exclude-size',
            action='store_true',
            help='Exclude groups where products have different sizes.'
        )

    def handle(self, *args, **options):
        if options['find']:
            self.find_duplicates(exclude_size=options['exclude_size'])

    def find_duplicates(self, exclude_size=False):
        self.stdout.write(self.style.SQL_FIELD('--- Finding potential duplicates by normalized name and brand ---'))

        # Group products by normalized name and brand
        product_groups = defaultdict(list)
        for product in Product.objects.all():
            normalized = normalize_name(product.name)
            brand = product.brand.lower() if product.brand else ''
            product_groups[(normalized, brand)].append(product)

        # Filter for groups with more than one product
        duplicate_groups = {key: products for key, products in product_groups.items() if len(products) > 1}

        # If --exclude-size is used, filter out groups with varying sizes
        if exclude_size:
            self.stdout.write(self.style.SQL_FIELD('--- Filtering: Excluding groups with different sizes ---'))
            filtered_groups = {}
            for key, products in duplicate_groups.items():
                # Create a set of all sizes in the group
                sizes = {p.size for p in products}
                # If there's only one unique size, keep the group
                if len(sizes) == 1:
                    filtered_groups[key] = products
            duplicate_groups = filtered_groups


        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS('No potential duplicates found with the current criteria.'))
            return

        self.stdout.write(f'Found {len(duplicate_groups)} potential duplicate groups.')
        
        for (normalized_name, brand), products in duplicate_groups.items():
            self.stdout.write(self.style.WARNING(f"\nGroup: Normalized Name='{normalized_name}', Brand='{brand}'"))
            for p in products:
                self.stdout.write(f"  - ID: {p.id}, Name: '{p.name}', Brand: '{p.brand}', Size: '{p.size}'")

        self.stdout.write(self.style.SUCCESS(f'\n--- Analysis complete. Found {len(duplicate_groups)} potential duplicate groups. ---'))