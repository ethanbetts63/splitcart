
from django.core.management.base import BaseCommand
from products.models import ProductBrand

class Command(BaseCommand):
    help = 'Checks for duplicate normalized_name_variations across different ProductBrand objects.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Checking for duplicate normalized name variations ---"))

        variations_map = {}
        duplicates_found = False

        all_brands = ProductBrand.objects.filter(normalized_name_variations__isnull=False)

        for brand in all_brands:
            if not brand.normalized_name_variations or not isinstance(brand.normalized_name_variations, list):
                continue

            for variation in brand.normalized_name_variations:
                if variation in variations_map:
                    # It's only a duplicate if it belongs to a different brand
                    if variations_map[variation]['id'] != brand.id:
                        duplicates_found = True
                        self.stdout.write(self.style.WARNING("--- DUPLICATE FOUND ---"))
                        self.stdout.write(f"  Variation: '{variation}'")
                        self.stdout.write(f"  Brand 1: '{variations_map[variation]['name']}' (ID: {variations_map[variation]['id']})")
                        self.stdout.write(f"  Brand 2: '{brand.name}' (ID: {brand.id})")
                        self.stdout.write("-----------------------")
                else:
                    variations_map[variation] = {'id': brand.id, 'name': brand.name}

        if not duplicates_found:
            self.stdout.write(self.style.SUCCESS("No duplicate normalized name variations found across different brands."))
        else:
            self.stdout.write(self.style.WARNING("Duplicate variations were found. Please review the output above."))
