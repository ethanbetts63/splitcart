from .base_translation_view import BaseTranslationView
from data_management.database_updating_classes.brand_translation_table_generator import BrandTranslationTableGenerator

class BrandTranslationView(BaseTranslationView):
    """
    Serves the brand name translation table.
    """
    generator_class = BrandTranslationTableGenerator
