import tempfile
import shutil
import json
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.process_store_file import process_store_file

class ProcessStoreFileTest(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_name = "store.json"
        self.file_path = os.path.join(self.test_dir, self.file_name)

        self.store_data = {
            "metadata": {"company": "TestCorp"},
            "store_data": {
                "store_id": "TC001",
                "store_name": "Test Store",
                "division": "Grocery"
            }
        }
        with open(self.file_path, 'w') as f:
            json.dump(self.store_data, f)

        self.mock_command = MagicMock()
        self.mock_tally = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('api.utils.database_updating_utils.process_store_file.get_or_create_store')
    @patch('api.utils.database_updating_utils.process_store_file.get_or_create_division')
    @patch('api.utils.database_updating_utils.process_store_file.get_or_create_company')
    def test_process_store_file_success(
        self, mock_get_or_create_company, mock_get_or_create_division, mock_get_or_create_store
    ):
        # Mock the return values of the helper functions
        mock_company = MagicMock()
        mock_get_or_create_company.return_value = (mock_company, True)
        mock_division = MagicMock()
        mock_get_or_create_division.return_value = (mock_division, True)
        mock_store = MagicMock()
        mock_get_or_create_store.return_value = (mock_store, True)

        process_store_file(self.file_name, self.test_dir, self.mock_command, self.mock_tally)

        # Assert that the helper functions were called correctly
        mock_get_or_create_company.assert_called_once_with("TestCorp")
        mock_get_or_create_division.assert_called_once()
        mock_get_or_create_store.assert_called_once()

        # Assert that the tally was incremented
        self.mock_tally.increment.assert_called_once_with(True, "TestCorp")

        # Assert that the file was removed
        self.assertFalse(os.path.exists(self.file_path))
