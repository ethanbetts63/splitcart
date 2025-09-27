from .base_python_file_view import BasePythonFileView
from data_management.database_updating_classes.brand_translation_table_generator import BrandTranslationTableGenerator

class BrandTranslationFileView(BasePythonFileView):
    """
    Serves the brand name translation table as a Python file.
    """
    generator_class = BrandTranslationTableGenerator
    variable_name = "BRAND_NAME_TRANSLATIONS"
