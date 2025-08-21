import re
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Extracts size from product name and updates the size field.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the process and show what would be changed.'
        )

    def _extract_size_from_name(self, name):
        extracted_sizes = []
        # More comprehensive list of units and their variations
        units = {
            'g': ['g', 'gram', 'grams'],
            'kg': ['kg', 'kilogram', 'kilograms'],
            'ml': ['ml', 'millilitre', 'millilitres'],
            'l': ['l', 'litre', 'litres'],
            'pk': ['pk', 'pack'],
            'ea': ['each', 'ea'],
        }

        # Build a regex pattern that is more robust
        # It looks for a number (integer or decimal) followed by an optional space and then a unit
        for standard_unit, variations in units.items():
            for unit in variations:
                # Match the unit as a whole word
                pattern = r'(\d+\.?\d*)\s*' + re.escape(unit) + r'\b'
                matches = re.finditer(pattern, name, re.IGNORECASE)
                for match in matches:
                    extracted_sizes.append(f"{match.group(1)}{standard_unit}")
        return extracted_sizes

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN ---"))

        products = Product.objects.all()
        total_products = products.count()

        for i, product in enumerate(products):
            extracted_size = self._extract_size_from_name(product.name)

            if extracted_sizes:
                if dry_run:
                    self.stdout.write(f"Product ID: {product.id}")
                    self.stdout.write(f"  Original Name: {product.name}")
                    self.stdout.write(f"  Original Sizes: {product.sizes}")
                    self.stdout.write(self.style.SUCCESS(f"  Extracted Sizes: {extracted_sizes}"))
                    self.stdout.write("--------------------")
                else:
                    # Add extracted sizes to the existing sizes list, avoiding duplicates
                    product.sizes = list(set(product.sizes + extracted_sizes))
                    product.save()
            
            if (i + 1) % 100 == 0 or (i + 1) == total_products:
                self.stdout.write(f"Processed {i + 1}/{total_products} products...")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Finished extracting sizes and updating products."))
