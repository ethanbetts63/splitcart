from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Checks for products that have more than one entry in their normalized_name_brand_size_variations list.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Variation Check ---"))

        products_with_multiple_variations = []
        
        # Use iterator for memory efficiency on large datasets
        for product in Product.objects.all().iterator():
            # Ensure the variations field is a list before checking its length
            variations = product.normalized_name_brand_size_variations
            if isinstance(variations, list) and len(variations) > 1:
                products_with_multiple_variations.append(product)

        count = len(products_with_multiple_variations)

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"Found {count} products with more than one variation string."))
            self.stdout.write("--- Example Products ---")
            for i, p in enumerate(products_with_multiple_variations[:5]): # Print up to 5 examples
                self.stdout.write(f"  - PK: {p.pk}, Name: {p.name}")
                self.stdout.write(f"    Variations: {p.normalized_name_brand_size_variations}")
        else:
            self.stdout.write(self.style.WARNING("No products found with more than one variation string."))

        self.stdout.write(self.style.SUCCESS("--- Variation Check Complete ---"))
