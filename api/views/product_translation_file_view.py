from .base_python_file_view import BasePythonFileView
from data_management.database_updating_classes.product_translation_table_generator import ProductTranslationTableGenerator

class ProductTranslationFileView(BasePythonFileView):
    """
    Serves the product name translation table as a Python file.
    """
    generator_class = ProductTranslationTableGenerator
    variable_name = "PRODUCT_NAME_TRANSLATIONS"
