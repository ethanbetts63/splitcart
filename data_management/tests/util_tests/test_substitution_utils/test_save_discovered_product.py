import json
import os
from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from data_management.utils.substitution_utils.save_discovered_product import save_discovered_product, DISCOVERED_PRODUCTS_FILE

class SaveDiscoveredProductTest(TestCase):
    @patch('data_management.utils.substitution_utils.save_discovered_product.os.makedirs')
    @patch('data_management.utils.substitution_utils.save_discovered_product.open', new_callable=mock_open)
    def test_save_discovered_product_new_product(self, mock_open_file, mock_makedirs):
        product_data = {"Stockcode": "prod1", "Name": "Product 1"}
        
        # Simulate empty file initially
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps([])

        save_discovered_product(product_data)

        mock_makedirs.assert_called_once_with(os.path.dirname(DISCOVERED_PRODUCTS_FILE), exist_ok=True)
        
        # Check the write calls
        written_data = "".join(c.args[0] for c in mock_open_file().write.call_args_list)
        self.assertEqual(written_data, json.dumps([product_data], indent=4))

    @patch('data_management.utils.substitution_utils.save_discovered_product.os.makedirs')
    @patch('data_management.utils.substitution_utils.save_discovered_product.open', new_callable=mock_open)
    def test_save_discovered_product_existing_product(self, mock_open_file, mock_makedirs):
        product_data = {"Stockcode": "prod1", "Name": "Product 1"}
        existing_data = [{"Stockcode": "prod1", "Name": "Product 1 Existing"}]
        
        # Simulate file with existing product
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(existing_data)

        save_discovered_product(product_data)

        mock_makedirs.assert_called_once_with(os.path.dirname(DISCOVERED_PRODUCTS_FILE), exist_ok=True)
        # Assert that write was not called, as product already exists
        self.assertFalse(mock_open_file().write.called)

    @patch('data_management.utils.substitution_utils.save_discovered_product.os.makedirs')
    @patch('data_management.utils.substitution_utils.save_discovered_product.open', new_callable=mock_open)
    def test_save_discovered_product_no_product_id(self, mock_open_file, mock_makedirs):
        product_data = {"Name": "Product without ID"}
        save_discovered_product(product_data)
        mock_makedirs.assert_not_called() # Should not even try to create dir
        self.assertFalse(mock_open_file().write.called)

    @patch('data_management.utils.substitution_utils.save_discovered_product.os.makedirs')
    @patch('data_management.utils.substitution_utils.save_discovered_product.open', new_callable=mock_open)
    def test_save_discovered_product_file_not_found_initially(self, mock_open_file, mock_makedirs):
        product_data = {"Stockcode": "prod1", "Name": "Product 1"}
        
        # Create a mock file handle for the write operation
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value = mock_file_handle # For context manager
        
        # Configure mock_open_file to raise FileNotFoundError on first read, then return mock_file_handle for writing
        mock_open_file.side_effect = [FileNotFoundError, mock_file_handle] # First call raises FileNotFoundError, second call returns mock_file_handle

        save_discovered_product(product_data)

        mock_makedirs.assert_called_once_with(os.path.dirname(DISCOVERED_PRODUCTS_FILE), exist_ok=True)
        written_data = "".join(c.args[0] for c in mock_file_handle.write.call_args_list) # Inspect mock_file_handle
        self.assertEqual(written_data, json.dumps([product_data], indent=4))

    @patch('data_management.utils.substitution_utils.save_discovered_product.os.makedirs')
    @patch('data_management.utils.substitution_utils.save_discovered_product.open', new_callable=mock_open)
    def test_save_discovered_product_json_decode_error_initially(self, mock_open_file, mock_makedirs):
        product_data = {"Stockcode": "prod1", "Name": "Product 1"}
        
        # Create a mock file handle for the write operation
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.return_value = mock_file_handle # For context manager

        # Configure mock_open_file to raise JSONDecodeError on first read, then return mock_file_handle for writing
        mock_open_file.side_effect = [json.JSONDecodeError("msg", "", 0), mock_file_handle] # First call raises JSONDecodeError, second call returns mock_file_handle

        save_discovered_product(product_data)

        mock_makedirs.assert_called_once_with(os.path.dirname(DISCOVERED_PRODUCTS_FILE), exist_ok=True)
        written_data = "".join(c.args[0] for c in mock_file_handle.write.call_args_list) # Inspect mock_file_handle
        self.assertEqual(written_data, json.dumps([product_data], indent=4))
