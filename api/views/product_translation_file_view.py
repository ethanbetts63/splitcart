from .base_python_file_view import BasePythonFileView
from data_management.database_updating_classes.translation_table_generators.product_translation_table_generator import ProductTranslationTableGenerator
from api.permissions import IsInternalAPIRequest

class ProductTranslationFileView(BasePythonFileView):
    """
    Serves the product name translation table as a Python file.
    """
    permission_classes = [IsInternalAPIRequest]
    generator_class = ProductTranslationTableGenerator
    variable_name = "PRODUCT_NAME_TRANSLATIONS"
