from django.db import transaction
from products.models import Product, ProductBrand
from api.data.brand_translation_table import BRAND_NAME_TRANSLATIONS

class BrandReconciler:
    def __init__(self, command):
        self.command = command

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Brand Reconciler run started."))
        
        if not BRAND_NAME_TRANSLATIONS:
            self.command.stdout.write("Brand translation table is empty. Nothing to reconcile.")
            return

        # These are the normalized names of brands that are variations.
        variation_keys = list(BRAND_NAME_TRANSLATIONS.keys())
        potential_duplicates = ProductBrand.objects.filter(normalized_name__in=variation_keys)

        if not potential_duplicates:
            self.command.stdout.write("No brands found matching any variation keys.")
            return

        self.command.stdout.write(f"Found {len(potential_duplicates)} potential duplicate brands to process.")

        for duplicate_brand in potential_duplicates:
            # Find the canonical key from the table
            canonical_key = BRAND_NAME_TRANSLATIONS.get(duplicate_brand.normalized_name)
            if not canonical_key:
                continue

            try:
                # Get the two brand objects
                canonical_brand = ProductBrand.objects.get(normalized_name=canonical_key)
                
                if canonical_brand.id == duplicate_brand.id:
                    continue

                self._merge_brands(canonical_brand, duplicate_brand)

            except ProductBrand.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Could not find canonical brand for key {canonical_key}. Skipping."))
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred for {duplicate_brand.normalized_name}: {e}"))
                continue

        self.command.stdout.write(self.command.style.SUCCESS("Brand Reconciler run finished."))

    @transaction.atomic
    def _merge_brands(self, canonical, duplicate):
        """
        Merges the duplicate brand into the canonical brand.
        """
        self.command.stdout.write(f"  - Merging brand '{duplicate.name}' into '{canonical.name}'")

        # 1. Update all products pointing to the duplicate brand's normalized_name
        Product.objects.filter(normalized_brand=duplicate.normalized_name).update(
            normalized_brand=canonical.normalized_name,
            brand=canonical.name
        )
        self.command.stdout.write(f"    - Updated associated products.")

        # 2. Merge name_variations lists
        if duplicate.name_variations:
            if not canonical.name_variations:
                canonical.name_variations = []
            for variation in duplicate.name_variations:
                if variation not in canonical.name_variations:
                    canonical.name_variations.append(variation)
        
        # 3. Merge normalized_name_variations lists
        if duplicate.normalized_name_variations:
            if not canonical.normalized_name_variations:
                canonical.normalized_name_variations = []
            for norm_variation in duplicate.normalized_name_variations:
                if norm_variation not in canonical.normalized_name_variations:
                    canonical.normalized_name_variations.append(norm_variation)

        # 4. Ensure the duplicate's own names are added to the variations list
        new_name_variation_entry = (duplicate.name, 'reconciler')
        if new_name_variation_entry not in canonical.name_variations:
            canonical.name_variations.append(new_name_variation_entry)
        
        if duplicate.normalized_name not in canonical.normalized_name_variations:
            canonical.normalized_name_variations.append(duplicate.normalized_name)

        canonical.save()
        self.command.stdout.write(f"    - Merged variation lists.")

        # 5. Delete the duplicate brand
        duplicate.delete()
        self.command.stdout.write(f"    - Deleted duplicate brand.")
