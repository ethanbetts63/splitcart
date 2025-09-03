
import os
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock, patch

from api.database_updating_classes.translation_table_generator import TranslationTableGenerator
from products.tests.test_helpers.model_factories import ProductFactory

class TranslationTableGeneratorTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.generator = TranslationTableGenerator(self.mock_command)
        
        # Create products with predictable names/brands
        p1 = ProductFactory(
            name='Item One', brand='Brand A', size='1kg',
            normalized_string_variations=['variation-a', 'variation-b']
        )
        p2 = ProductFactory(
            name='Item Two', brand='Brand B', size='2L'
        )
        # Set variations after creation to use the generated canonical name
        p2.normalized_string_variations=['variation-c', p2.normalized_name_brand_size.upper()]
        p2.save()
        ProductFactory(
            name='Item Three', brand='Brand C', size='3 each',
            normalized_string_variations=[] # Test product with no variations
        )

        # Dynamically define the expected output based on the created products
        global EXPECTED_TRANSLATIONS
        EXPECTED_TRANSLATIONS = {
            'variation-a': p1.normalized_name_brand_size,
            'variation-b': p1.normalized_name_brand_size,
            'variation-c': p2.normalized_name_brand_size,
        }

    @patch('api.database_updating_classes.translation_table_generator.open', new_callable=MagicMock)
    def test_generate_creates_correct_table(self, mock_open):
        """Test that the translation table is generated with the correct content."""
        self.generator.generate()

        # Check that open was called correctly
        mock_open.assert_called_once()

        # Get all the content that was written
        written_content = "".join(call.args[0] for call in mock_open().write.call_args_list)

        self.assertIn("PRODUCT_NAME_TRANSLATIONS = {", written_content)
        for key, value in EXPECTED_TRANSLATIONS.items():
            self.assertIn(f"    '{key}': '{value}',", written_content)
        self.assertNotIn('CANONICAL-TWO', written_content)

    @patch('builtins.open', side_effect=IOError('Test IO Error'))
    def test_generate_handles_io_error(self, mock_open):
        """Test that an IOError during file writing is handled gracefully."""
        self.generator.generate()
        self.mock_command.stderr.write.assert_called_once()
