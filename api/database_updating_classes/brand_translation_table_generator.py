import os
from products.models import Brand as ProductBrand
from .base_translation_table_generator import BaseTranslationTableGenerator

# Define the output path relative to this file's location
TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'generated_brand_synonyms.py'
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
            variable_name="BRAND_SYNONYMS"
        )

    def generate_translation_dict(self) -> dict:
        """
        Queries all ProductBrand objects and builds a translation dictionary
        from their name variations.

        Returns:
            A dictionary mapping brand variations to canonical brand names.
        """
        print("--- Generating brand synonym translation dictionary ---")
        synonyms = {}

        # Query all brands that have variations defined
        all_brands = ProductBrand.objects.filter(name_variations__isnull=False)

        for brand in all_brands:
            canonical_name = brand.name
            if not brand.name_variations or not isinstance(brand.name_variations, list):
                continue

            for variation in brand.name_variations:
                if variation.lower() != canonical_name.lower():
                    synonyms[variation] = canonical_name
        
        print(f"Generated {len(synonyms)} brand synonyms.")
        return synonyms
