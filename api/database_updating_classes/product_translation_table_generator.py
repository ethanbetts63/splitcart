import os
from products.models import Product
from .base_translation_table_generator import BaseTranslationTableGenerator

# Define the output path relative to this file's location
TRANSLATION_TABLE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
    'data',
    'product_name_translation_table.py'
))

class ProductTranslationTableGenerator(BaseTranslationTableGenerator):
    """
    Generates a translation table for product name variations.
    """
    def __init__(self):
        """
        Initializes the generator for product name translations.
        """
        super().__init__(
            output_path=TRANSLATION_TABLE_PATH,
            variable_name="PRODUCT_NAME_TRANSLATIONS"
        )

    def generate_translation_dict(self) -> dict:
        """
        Queries all products and builds a translation dictionary from their
        normalized name variations.

        Returns:
            A dictionary mapping variation strings to canonical strings.
        """
        print("--- Generating product name translation dictionary ---")
        translations = {}
        all_products = Product.objects.all()

        for product in all_products:
            if not product.normalized_name_brand_size_variations or not isinstance(product.normalized_name_brand_size_variations, list):
                continue

            canonical_normalized_string = product.normalized_name_brand_size
            if not canonical_normalized_string:
                continue

            for variation_normalized_string in product.normalized_name_brand_size_variations:
                if variation_normalized_string.lower() != canonical_normalized_string.lower():
                    translations[variation_normalized_string] = canonical_normalized_string
        
        print(f"Generated {len(translations)} product name translations.")
        return translations
