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
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    # Return the number and the standard unit
                    return f"{match.group(1)}{standard_unit}"
        return None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN ---"))

        products = Product.objects.all()
        total_products = products.count()

        for i, product in enumerate(products):
            extracted_size = self._extract_size_from_name(product.name)

            if extracted_size:
                if dry_run:
                    self.stdout.write(f"Product ID: {product.id}")
                    self.stdout.write(f"  Original Name: {product.name}")
                    self.stdout.write(f"  Original Size: {product.size}")
                    self.stdout.write(self.style.SUCCESS(f"  Extracted Size: {extracted_size}"))
                    self.stdout.write("--------------------")
                else:
                    product.size = extracted_size
                    product.save()
            
            if (i + 1) % 100 == 0 or (i + 1) == total_products:
                self.stdout.write(f"Processed {i + 1}/{total_products} products...")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Finished extracting sizes and updating products."))
