from .base_translation_view import BaseTranslationView
from data_management.database_updating_classes.product_translation_table_generator import ProductTranslationTableGenerator

class ProductTranslationView(BaseTranslationView):
    """
    Serves the product name translation table.
    """
    generator_class = ProductTranslationTableGenerator
