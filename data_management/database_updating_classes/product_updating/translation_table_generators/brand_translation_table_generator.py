import os
from products.models import Product, ProductBrand
from .base_translation_table_generator import BaseTranslationTableGenerator

# Define the output path relative to this file's location
TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    '..',
    '..',
    'data',
    'brand_translation_table.py'
))

class BrandTranslationTableGenerator(BaseTranslationTableGenerator):
    """
    Generates a translation table for product brand synonyms.
    """
    def __init__(self):
        """
        Initializes the generator for brand synonyms.
        """
        super().__init__(
            output_path=TRANSLATION_TABLE_PATH,
            variable_name="BRAND_NAME_TRANSLATIONS"
        )

    def generate_translation_dict(self) -> dict:
        """
        Queries all ProductBrand objects and builds a translation dictionary
        from their normalized name variations. It includes logic to detect and
        resolve circular dependencies, ensuring a clean, directed graph of brand synonyms.

        Returns:
            A dictionary mapping normalized brand variations to normalized canonical brand names.
        """
        print("--- Generating brand synonym translation dictionary ---")
        
        all_brands = list(ProductBrand.objects.all())
        brand_map = {brand.normalized_name: brand for brand in all_brands}
        
        synonyms = {}
        conflicts = []

        # First pass: gather all potential mappings and identify circular dependencies
        print("--- Identifying synonyms and conflicts ---")
        for brand in all_brands:
            canonical_name = brand.normalized_name
            if not brand.normalized_name_variations or not isinstance(brand.normalized_name_variations, list):
                continue

            for variation_name in brand.normalized_name_variations:
                if variation_name == canonical_name:
                    continue

                # Check for circular dependency: if a variation is a canonical brand that points back to the current brand
                if variation_name in brand_map:
                    conflicting_brand = brand_map[variation_name]
                    if conflicting_brand.normalized_name_variations and canonical_name in conflicting_brand.normalized_name_variations:
                        conflict_pair = tuple(sorted((canonical_name, variation_name)))
                        if conflict_pair not in conflicts:
                            conflicts.append(conflict_pair)
                        continue  # Skip adding to synonyms for now; will be resolved later

                # Check if this variation is already mapped to a different canonical name
                if variation_name in synonyms and synonyms[variation_name] != canonical_name:
                    print(f"  - Warning: Variation '{variation_name}' is ambiguously mapped to both '{synonyms[variation_name]}' and '{canonical_name}'.")
                    # For now, the last one wins, but this could be a point for future improvement.
                
                synonyms[variation_name] = canonical_name

        # Second pass: resolve circular dependencies using a tie-breaking mechanism
        if conflicts:
            print(f"--- Resolving {len(conflicts)} circular dependencies ---")
            for brand1_name, brand2_name in conflicts:
                brand1 = brand_map[brand1_name]
                brand2 = brand_map[brand2_name]

                winner, loser = self._resolve_conflict(brand1, brand2)
                
                print(f"  - Conflict: '{brand1.name}' <-> '{brand2.name}'. Winner determined to be '{winner.name}'.")
                
                # The loser's normalized name should map to the winner's normalized name
                synonyms[loser.normalized_name] = winner.normalized_name
                # Ensure the winner does not point back to the loser
                if winner.normalized_name in synonyms:
                    del synonyms[winner.normalized_name]

        print(f"--- Generated {len(synonyms)} brand synonyms. ---")
        return synonyms

    def _resolve_conflict(self, brand1, brand2):
        """
        Resolves a conflict between two brands that have a circular dependency.
        Returns a tuple of (winner, loser).
        """
        # Tie-breaker 1: Confirmed Prefix (from GS1 data)
        b1_has_prefix = bool(brand1.confirmed_official_prefix)
        b2_has_prefix = bool(brand2.confirmed_official_prefix)
        if b1_has_prefix and not b2_has_prefix:
            return brand1, brand2
        if b2_has_prefix and not b1_has_prefix:
            return brand2, brand1

        # Tie-breaker 2: Product Count
        # Note: This can be slow if run for many conflicts.
        b1_products = Product.objects.filter(brand=brand1).count()
        b2_products = Product.objects.filter(brand=brand2).count()
        if b1_products > b2_products:
            return brand1, brand2
        if b2_products > b1_products:
            return brand2, brand1

        # Tie-breaker 3: Variation Count
        b1_variations = len(brand1.name_variations) if brand1.name_variations else 0
        b2_variations = len(brand2.name_variations) if brand2.name_variations else 0
        if b1_variations > b2_variations:
            return brand1, brand2
        if b2_variations > b1_variations:
            return brand2, brand1

        # Tie-breaker 4: Alphabetical by name
        if brand1.name < brand2.name:
            return brand1, brand2
        else:
            return brand2, brand1
