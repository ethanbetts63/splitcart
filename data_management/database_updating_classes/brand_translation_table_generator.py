import os
from products.models import ProductBrand
from .base_translation_table_generator import BaseTranslationTableGenerator

# Define the output path relative to this file's location
TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
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
        from their normalized name variations.

        Returns:
            A dictionary mapping normalized brand variations to normalized canonical brand names.
        """
        print("--- Generating brand synonym translation dictionary ---")
        synonyms = {}

        # Query all brands that have variations defined
        all_brands = ProductBrand.objects.filter(normalized_name_variations__isnull=False)

        for brand in all_brands:
            # The canonical name is the brand's own normalized name
            canonical_normalized = brand.normalized_name
            
            if not brand.normalized_name_variations or not isinstance(brand.normalized_name_variations, list):
                continue

            for normalized_variation in brand.normalized_name_variations:
                # Map the normalized variation to the canonical normalized name
                if normalized_variation != canonical_normalized:
                    synonyms[normalized_variation] = canonical_normalized
        
        print(f"Generated {len(synonyms)} brand synonyms.")
        return synonyms
