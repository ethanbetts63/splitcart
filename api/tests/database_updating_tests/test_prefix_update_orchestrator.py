import os
import json
from django.test import TestCase, override_settings
from unittest.mock import Mock, patch, call

from api.database_updating_classes.prefix_update_orchestrator import PrefixUpdateOrchestrator
from products.models import ProductBrand, BrandPrefix
from products.tests.test_helpers.model_factories import ProductBrandFactory, BrandPrefixFactory

# Use a temporary directory for these tests that is independent of the project structure
TEST_INBOX_DIR = 'test_inbox'
TEST_TEMP_DIR = 'test_temp_storage'

@override_settings(BASE_DIR=os.getcwd()) # Ensure BASE_DIR is correct for tests
class PrefixUpdateOrchestratorTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        # Create the temp directories for the test run
        os.makedirs(TEST_INBOX_DIR, exist_ok=True)
        os.makedirs(TEST_TEMP_DIR, exist_ok=True)
        self.orchestrator = PrefixUpdateOrchestrator(self.mock_command)
        # Override paths to use our test directories
        self.orchestrator.inbox_path = TEST_INBOX_DIR
        self.orchestrator.temp_storage_path = TEST_TEMP_DIR

    def tearDown(self):
        # Clean up the temporary directories
        for root, dirs, files in os.walk(TEST_INBOX_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(TEST_INBOX_DIR)

        for root, dirs, files in os.walk(TEST_TEMP_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(TEST_TEMP_DIR)

    def test_run_no_files(self):
        """Test that the orchestrator runs cleanly when the inbox is empty."""
        self.orchestrator.run()
        # Check that stdout shows the inbox is empty
        self.mock_command.stdout.write.assert_any_call("Prefix inbox is empty. No new data to process.")

    @patch('api.database_updating_classes.prefix_update_orchestrator.generate_brand_synonym_file')
    @patch('api.database_updating_classes.prefix_update_orchestrator.VariationManager')
    def test_run_updates_brand_prefix_and_moves_file(self, mock_variation_manager, mock_synonym_generator):
        """Test the happy path: a file is processed, DB is updated, and file is moved."""
        # 1. Arrange
        # Create a brand that the inbox file will reference
        target_brand = ProductBrandFactory(name='Original Brand Name')
        self.assertEqual(BrandPrefix.objects.count(), 0)

        # Create a fake inbox file
        file_path = os.path.join(TEST_INBOX_DIR, 'test.jsonl')
        record = {
            'target_brand_id': target_brand.id,
            'target_brand_name': 'Original Brand Name',
            'confirmed_license_key': '1234567',
            'confirmed_company_name': 'Official GS1 Name'
        }
        with open(file_path, 'w') as f:
            f.write(json.dumps(record) + '\n')

        # 2. Act
        self.orchestrator.run()

        # 3. Assert
        # Check that the BrandPrefix was created/updated and linked to the CANONICAL brand
        self.assertEqual(BrandPrefix.objects.count(), 1)

        # Find the canonical brand created by the orchestrator
        canonical_brand = ProductBrand.objects.get(name='Official GS1 Name')

        # Check that the prefix is linked to this canonical brand
        brand_prefix = BrandPrefix.objects.get(brand=canonical_brand)
        self.assertEqual(brand_prefix.confirmed_official_prefix, '1234567')
        self.assertEqual(brand_prefix.brand_name_gs1, 'Official GS1 Name')

        # Also assert that the original brand still exists
        self.assertTrue(ProductBrand.objects.filter(name='Original Brand Name').exists())

        # Check that the file was moved
        self.assertFalse(os.path.exists(file_path))
        self.assertTrue(os.path.exists(os.path.join(TEST_TEMP_DIR, 'test.jsonl')))

        # Check that brand reconciliation was triggered
        mock_variation_manager.return_value.reconcile_brand_duplicates.assert_called_once()

        # Check that the synonym file generation was triggered
        mock_synonym_generator.assert_called_once_with(self.mock_command)

    def test_process_record_skips_missing_data(self):
        """Test that records with incomplete data are skipped."""
        brand_reconciliation_list = []
        invalid_record = {'target_brand_id': 1} # Missing other keys
        self.orchestrator._process_record(invalid_record, brand_reconciliation_list)
        self.mock_command.stderr.write.assert_called_once()
        self.assertEqual(len(brand_reconciliation_list), 0)
        self.assertEqual(BrandPrefix.objects.count(), 0)

    def test_process_record_skips_brand_not_found(self):
        """Test that records referencing a non-existent brand are skipped."""
        brand_reconciliation_list = []
        record = {
            'target_brand_id': 999, # Does not exist
            'target_brand_name': 'Original Brand Name',
            'confirmed_license_key': '1234567',
            'confirmed_company_name': 'Official GS1 Name'
        }
        self.orchestrator._process_record(record, brand_reconciliation_list)
        self.mock_command.stderr.write.assert_called_once()
        self.assertEqual(len(brand_reconciliation_list), 0)
        self.assertEqual(BrandPrefix.objects.count(), 0)
