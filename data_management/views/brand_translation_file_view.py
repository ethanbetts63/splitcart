from .base_python_file_view import BasePythonFileView
from data_management.database_updating_classes.product_updating.translation_table_generators.brand_translation_table_generator import BrandTranslationTableGenerator
from splitcart.permissions import IsInternalAPIRequest

class BrandTranslationFileView(BasePythonFileView):
    """
    Serves the brand name translation table as a Python file.
    """
    permission_classes = [IsInternalAPIRequest]
    generator_class = BrandTranslationTableGenerator
    variable_name = "BRAND_NAME_TRANSLATIONS"
