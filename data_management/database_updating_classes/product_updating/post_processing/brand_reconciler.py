import os
from django.db import transaction
from products.models import Product, ProductBrand
from .base_reconciler import BaseReconciler

TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'brand_translation_table.py'
))

class BrandReconciler(BaseReconciler):
    def __init__(self, command):
        super().__init__(command, TRANSLATION_TABLE_PATH)

    def get_model(self):
        return ProductBrand

    def get_variation_field_name(self):
        return 'normalized_name'

    def get_canonical_field_name(self):
        return 'normalized_name'

    @transaction.atomic
    def merge_items(self, canonical_item, duplicate_item):
        """
        Merges the duplicate brand into the canonical brand.
        """
        self.command.stdout.write(f"  - Merging brand '{duplicate_item.name}' into '{canonical_item.name}'")

        Product.objects.filter(brand=duplicate_item).update(brand=canonical_item)

        if duplicate_item.name_variations:
            if not canonical_item.name_variations:
                canonical_item.name_variations = []
            for variation in duplicate_item.name_variations:
                if variation not in canonical_item.name_variations:
                    canonical_item.name_variations.append(variation)
        
        if duplicate_item.normalized_name_variations:
            if not canonical_item.normalized_name_variations:
                canonical_item.normalized_name_variations = []
            for norm_variation in duplicate_item.normalized_name_variations:
                if norm_variation not in canonical_item.normalized_name_variations:
                    canonical_item.normalized_name_variations.append(norm_variation)

        new_name_variation_entry = duplicate_item.name
        if new_name_variation_entry not in canonical_item.name_variations:
            canonical_item.name_variations.append(new_name_variation_entry)
        
        if duplicate_item.normalized_name not in canonical_item.normalized_name_variations:
            canonical_item.normalized_name_variations.append(duplicate_item.normalized_name)

        canonical_item.save()