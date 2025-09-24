import os
import ast
from django.db import transaction
from products.models import Product, ProductBrand

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'brand_translation_table.py'
))

class BrandReconciler:
    def __init__(self, command):
        self.command = command

    def _load_translation_table(self):
        """
        Safely loads the BRAND_NAME_TRANSLATIONS dictionary from the .py file.
        """
        try:
            with open(TRANSLATION_TABLE_PATH, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            if '=' in file_content:
                dict_str = file_content.split('=', 1)[1].strip()
                return ast.literal_eval(dict_str)
            return {}
        except (FileNotFoundError, SyntaxError, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"Error loading brand translation table: {e}"))
            return {}

    def run(self):
        self.command.stdout.write(self.command.style.SUCCESS("Brand Reconciler run started."))
        
        brand_translations = self._load_translation_table()

        if not brand_translations:
            self.command.stdout.write("Brand translation table is empty or could not be loaded. Nothing to reconcile.")
            return

        variation_keys = list(brand_translations.keys())
        potential_duplicates = ProductBrand.objects.filter(normalized_name__in=variation_keys)

        if not potential_duplicates:
            self.command.stdout.write("No brands found matching any variation keys.")
            return

        self.command.stdout.write(f"Found {len(potential_duplicates)} potential duplicate brands to process.")

        brands_to_delete = []
        for duplicate_brand in potential_duplicates:
            canonical_key = brand_translations.get(duplicate_brand.normalized_name)
            if not canonical_key:
                continue

            try:
                canonical_brand = ProductBrand.objects.get(normalized_name=canonical_key)
                
                if canonical_brand.id == duplicate_brand.id:
                    continue

                self._merge_brands(canonical_brand, duplicate_brand, brands_to_delete)

            except ProductBrand.DoesNotExist:
                self.command.stderr.write(self.command.style.ERROR(f"Could not find canonical brand for key {canonical_key}. Skipping."))
                continue
            except Exception as e:
                self.command.stderr.write(self.command.style.ERROR(f"An unexpected error occurred for {duplicate_brand.normalized_name}: {e}"))
                continue

        if brands_to_delete:
            self.command.stdout.write(f"--- Deleting {len(brands_to_delete)} merged brands ---")
            for brand in brands_to_delete:
                brand.delete()


        self.command.stdout.write(self.command.style.SUCCESS("Brand Reconciler run finished."))

    @transaction.atomic
    def _merge_brands(self, canonical, duplicate, brands_to_delete: list):
        """
        Merges the duplicate brand into the canonical brand.
        """
        self.command.stdout.write(f"  - Merging brand '{duplicate.name}' into '{canonical.name}'")

        Product.objects.filter(brand=duplicate).update(brand=canonical)

        if duplicate.name_variations:
            if not canonical.name_variations:
                canonical.name_variations = []
            for variation in duplicate.name_variations:
                if variation not in canonical.name_variations:
                    canonical.name_variations.append(variation)
        
        if duplicate.normalized_name_variations:
            if not canonical.normalized_name_variations:
                canonical.normalized_name_variations = []
            for norm_variation in duplicate.normalized_name_variations:
                if norm_variation not in canonical.normalized_name_variations:
                    canonical.normalized_name_variations.append(norm_variation)

        new_name_variation_entry = duplicate.name
        if new_name_variation_entry not in canonical.name_variations:
            canonical.name_variations.append(new_name_variation_entry)
        
        if duplicate.normalized_name not in canonical.normalized_name_variations:
            canonical.normalized_name_variations.append(duplicate.normalized_name)

        canonical.save()

        if duplicate not in brands_to_delete:
            brands_to_delete.append(duplicate)