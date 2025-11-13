import os
from django.db import transaction
from products.models import Product, ProductBrand
import ast

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'brand_translation_table.py'
))

class BrandReconciler:
    """
    Finds and merges duplicate ProductBrand objects based on a translation table.
    This is a self-contained process that runs after all products have been updated.
    """
    def __init__(self, command):
        self.command = command
        self.translation_table_path = TRANSLATION_TABLE_PATH

    def _load_translation_table(self):
        """Safely loads the translation dictionary from the .py file."""
        try:
            with open(self.translation_table_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            if '=' in file_content:
                dict_str = file_content.split('=', 1)[1].strip()
                return ast.literal_eval(dict_str)
            return {}
        except (FileNotFoundError, SyntaxError, ValueError) as e:
            self.command.stderr.write(self.command.style.ERROR(f"Error loading brand translation table: {e}"))
            return {}

    def run(self):
        """
        Orchestrates the entire brand reconciliation process.
        """
        self.command.stdout.write("--- Brand Reconciler run started. ---")
        translations = self._load_translation_table()
        if not translations:
            self.command.stdout.write("Brand translation table is empty or could not be loaded. Nothing to reconcile.")
            return

        variation_names = list(translations.keys())
        canonical_names = list(set(translations.values()))

        all_brands = list(ProductBrand.objects.filter(
            normalized_name__in=variation_names + canonical_names
        ))

        brand_map = {brand.normalized_name: brand for brand in all_brands}
        
        brands_to_update = {}  # {canonical_id: canonical_obj}
        fk_updates = {}  # {canonical_id: [list_of_duplicate_ids]}
        brands_to_delete_ids = set()

        for variation_name, canonical_name in translations.items():
            duplicate_brand = brand_map.get(variation_name)
            canonical_brand = brand_map.get(canonical_name)

            if not duplicate_brand or not canonical_brand or duplicate_brand.id == canonical_brand.id:
                continue

            # Stage FK update
            fk_updates.setdefault(canonical_brand.id, []).append(duplicate_brand.id)
            
            # Stage deletion
            brands_to_delete_ids.add(duplicate_brand.id)

            # Stage update of canonical brand's variations
            if canonical_brand.id not in brands_to_update:
                brands_to_update[canonical_brand.id] = canonical_brand
            
            canon_obj = brands_to_update[canonical_brand.id]
            # Ensure variation lists exist
            canon_obj.name_variations = canon_obj.name_variations or []
            canon_obj.normalized_name_variations = canon_obj.normalized_name_variations or []

            # Merge variations
            if duplicate_brand.name not in canon_obj.name_variations:
                canon_obj.name_variations.append(duplicate_brand.name)
            if duplicate_brand.normalized_name not in canon_obj.normalized_name_variations:
                canon_obj.normalized_name_variations.append(duplicate_brand.normalized_name)
            
            if duplicate_brand.name_variations:
                for v in duplicate_brand.name_variations:
                    if v not in canon_obj.name_variations:
                        canon_obj.name_variations.append(v)
            if duplicate_brand.normalized_name_variations:
                for v in duplicate_brand.normalized_name_variations:
                    if v not in canon_obj.normalized_name_variations:
                        canon_obj.normalized_name_variations.append(v)

        if not brands_to_delete_ids:
            self.command.stdout.write("No brand duplicates found to merge.")
            return

        self.command.stdout.write(f"Found {len(brands_to_delete_ids)} duplicate brands to merge.")

        try:
            with transaction.atomic():
                # 1. Update foreign keys on Product table
                self.command.stdout.write("  - Re-assigning products from duplicate brands...")
                for canon_id, dupe_ids in fk_updates.items():
                    Product.objects.filter(brand_id__in=dupe_ids).update(brand_id=canon_id)

                # 2. Update canonical brands with new variations
                if brands_to_update:
                    # Sort the variation lists before saving
                    for brand in brands_to_update.values():
                        brand.name_variations = sorted(list(set(brand.name_variations)))
                        brand.normalized_name_variations = sorted(list(set(brand.normalized_name_variations)))
                    
                    ProductBrand.objects.bulk_update(
                        brands_to_update.values(),
                        ['name_variations', 'normalized_name_variations'],
                        batch_size=500
                    )
                    self.command.stdout.write(f"  - Bulk updated {len(brands_to_update)} canonical brands.")

                # 3. Delete the duplicate brands
                ProductBrand.objects.filter(id__in=brands_to_delete_ids).delete()
                self.command.stdout.write(f"  - Bulk deleted {len(brands_to_delete_ids)} duplicate brands.")

            self.command.stdout.write(self.command.style.SUCCESS("Brand reconciliation completed successfully."))

        except Exception as e:
            self.command.stderr.write(self.command.style.ERROR(f"An error occurred during brand reconciliation: {e}"))
            raise
