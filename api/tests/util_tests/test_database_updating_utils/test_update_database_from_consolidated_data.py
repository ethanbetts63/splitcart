
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.update_database_from_consolidated_data import update_database_from_consolidated_data

class UpdateDatabaseFromConsolidatedDataTest(TestCase):
    def setUp(self):
        self.mock_command = MagicMock()
        self.consolidated_data = {"product1": {}}
        self.processed_files = ["file1.json", "file2.json"]

    @patch('api.utils.database_updating_utils.update_database_from_consolidated_data.batch_create_category_relationships')
    @patch('api.utils.database_updating_utils.update_database_from_consolidated_data.batch_create_prices')
    @patch('api.utils.database_updating_utils.update_database_from_consolidated_data.batch_create_new_products')
    @patch('os.remove')
    def test_successful_update(self, mock_os_remove, mock_batch_create_new_products, mock_batch_create_prices, mock_batch_create_category_relationships):
        product_cache = {"product1": MagicMock()}
        mock_batch_create_new_products.return_value = product_cache

        update_database_from_consolidated_data(self.consolidated_data, self.processed_files, self.mock_command)

        mock_batch_create_new_products.assert_called_once_with(self.mock_command, self.consolidated_data)
        mock_batch_create_prices.assert_called_once_with(self.mock_command, self.consolidated_data, product_cache)
        mock_batch_create_category_relationships.assert_called_once_with(self.consolidated_data, product_cache)

        self.assertEqual(mock_os_remove.call_count, 2)
        mock_os_remove.assert_any_call("file1.json")
        mock_os_remove.assert_any_call("file2.json")

    @patch('api.utils.database_updating_utils.update_database_from_consolidated_data.batch_create_new_products', side_effect=Exception("DB Error"))
    @patch('os.remove')
    def test_failed_update(self, mock_os_remove, mock_batch_create_new_products):
        update_database_from_consolidated_data(self.consolidated_data, self.processed_files, self.mock_command)

        mock_batch_create_new_products.assert_called_once()
        mock_os_remove.assert_not_called()
        self.mock_command.stderr.write.assert_called_once()
