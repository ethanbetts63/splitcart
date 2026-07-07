from .base_python_file_view import BasePythonFileView
from pipeline.database_updating_classes.product_updating.translation_table_generators.product_translation_table_generator import ProductTranslationTableGenerator
from config.permissions import IsInternalAPIRequest

class ProductTranslationFileView(BasePythonFileView):
    """
    Serves the product name translation table as a JSON file.
    """
    permission_classes = [IsInternalAPIRequest]
    generator_class = ProductTranslationTableGenerator
