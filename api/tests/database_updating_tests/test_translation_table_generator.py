
import os
import tempfile
from django.test import TestCase
from unittest.mock import MagicMock, patch

from api.database_updating_classes.translation_table_generator import TranslationTableGenerator
from products.tests.test_helpers.model_factories import ProductFactory

# This is the dictionary we expect to be generated in the test
EXPECTED_TRANSLATIONS = {}

class TranslationTableGeneratorTests(TestCase):

    def setUp(self):
        self.mock_command = MagicMock()
        self.generator = TranslationTableGenerator(self.mock_command)
        # Create products that will be used to generate the translation table
        p1 = ProductFactory(
            name='canonical-one',
            brand='brand-one',
            normalized_name_brand_size='canonical-one',
            normalized_string_variations=['variation-a', 'variation-b']
        )
        p2 = ProductFactory(
            name='canonical-two',
            brand='brand-two',
            normalized_name_brand_size='canonical-two',
            normalized_string_variations=['variation-c', 'CANONICAL-TWO'] # Test case-insensitivity
        )
        p3 = ProductFactory(
            name='canonical-three',
            brand='brand-three',
            normalized_name_brand_size='canonical-three',
            normalized_string_variations=[] # Test product with no variations
        )

        # Define the expected output based on the products created
        global EXPECTED_TRANSLATIONS
        EXPECTED_TRANSLATIONS = {
            'variation-a': 'canonical-one',
            'variation-b': 'canonical-one',
            'variation-c': 'canonical-two',
        }

    @patch('api.database_updating_classes.translation_table_generator.TRANSLATION_TABLE_PATH')
    def test_generate_creates_correct_table(self, mock_path):
        """Test that the translation table is generated with the correct content."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.py') as tmp_file:
            mock_path.return_value = tmp_file.name
            # For the purpose of this test, we'll point the generator to our temp file
            self.generator.generate()

            # Now, read the content of the generated file and execute it to get the dictionary
            tmp_file.seek(0)
            generated_content = tmp_file.read()
            
            # A simple way to check the content without complex parsing
            self.assertIn("PRODUCT_NAME_TRANSLATIONS = {", generated_content)
            for key, value in EXPECTED_TRANSLATIONS.items():
                self.assertIn(f"    '{key}': '{value}',", generated_content)
            self.assertNotIn('CANONICAL-TWO', generated_content) # Check case-insensitive exclusion

        os.unlink(tmp_file.name)

    @patch('builtins.open', side_effect=IOError('Test IO Error'))
    def test_generate_handles_io_error(self, mock_open):
        """Test that an IOError during file writing is handled gracefully."""
        self.generator.generate()
        self.mock_command.stderr.write.assert_called_once()
        self.assertIn("Could not write to translation table file", self.mock_command.stderr.write.call_args[0][0])
