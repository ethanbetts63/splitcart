
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.update_products_from_inbox import update_products_from_inbox

class UpdateProductsFromInboxTest(TestCase):
    def setUp(self):
        self.mock_command = MagicMock()

    @patch('api.utils.database_updating_utils.update_products_from_inbox.update_database_from_consolidated_data')
    @patch('api.utils.database_updating_utils.update_products_from_inbox.consolidate_inbox_data')
    @patch('time.sleep')
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_update_products_from_inbox(self, mock_exists, mock_listdir, mock_sleep, mock_consolidate, mock_update):
        mock_listdir.side_effect = [["file1.jsonl"], []]
        consolidated_data = {"product1": {}}
        processed_files = ["file1.jsonl"]
        mock_consolidate.return_value = (consolidated_data, processed_files)

        update_products_from_inbox(self.mock_command)

        mock_consolidate.assert_called_once()
        mock_update.assert_called_once_with(consolidated_data, processed_files, self.mock_command)
        mock_sleep.assert_called_once_with(30)

    @patch('api.utils.database_updating_utils.update_products_from_inbox.update_database_from_consolidated_data')
    @patch('api.utils.database_updating_utils.update_products_from_inbox.consolidate_inbox_data')
    @patch('time.sleep')
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_no_files_initially_then_files_appear(self, mock_exists, mock_listdir, mock_sleep, mock_consolidate, mock_update):
        mock_listdir.side_effect = [[], ["file1.jsonl"], []]
        consolidated_data = {"product1": {}}
        processed_files = ["file1.jsonl"]
        mock_consolidate.return_value = (consolidated_data, processed_files)

        update_products_from_inbox(self.mock_command)

        mock_consolidate.assert_called_once()
        mock_update.assert_called_once()

    @patch('time.sleep')
    @patch('os.listdir')
    @patch('os.path.exists', return_value=True)
    def test_no_files_at_all(self, mock_exists, mock_listdir, mock_sleep):
        mock_listdir.return_value = []
        update_products_from_inbox(self.mock_command)
        mock_sleep.assert_called_once_with(30)
