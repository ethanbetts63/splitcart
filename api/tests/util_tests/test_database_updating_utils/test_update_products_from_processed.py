import os
import json
from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
from api.utils.database_updating_utils.update_products_from_processed import update_products_from_processed

class UpdateProductsFromProcessedTest(TestCase):
    @patch('api.utils.database_updating_utils.update_products_from_processed.os.listdir')
    @patch('api.utils.database_updating_utils.update_products_from_processed.os.path.exists')
    @patch('api.utils.database_updating_utils.update_products_from_processed.open', new_callable=mock_open)
    @patch('api.utils.database_updating_utils.update_products_from_processed.os.remove')
    @patch('api.utils.database_updating_utils.update_products_from_processed.os.makedirs')
    @patch('api.utils.database_updating_utils.update_products_from_processed.get_or_create_company')
    @patch('api.utils.database_updating_utils.update_products_from_processed.get_or_create_store')
    @patch('api.utils.database_updating_utils.update_products_from_processed.get_or_create_category_hierarchy')
    @patch('api.utils.database_updating_utils.update_products_from_processed.get_or_create_product')
    @patch('api.utils.database_updating_utils.update_products_from_processed.create_price')
    @patch('api.utils.database_updating_utils.update_products_from_processed.transaction.atomic')
    def test_update_products_from_processed_success(self, mock_atomic, mock_create_price, mock_get_or_create_product,
                                                    mock_get_or_create_category_hierarchy, mock_get_or_create_store,
                                                    mock_get_or_create_company, mock_makedirs, mock_os_remove,
                                                    mock_open_file, mock_os_path_exists, mock_os_listdir):

        # Mock command object
        mock_command = MagicMock()
        mock_command.stdout = MagicMock()
        mock_command.stderr = MagicMock()
        mock_command.style = MagicMock()
        mock_command.style.WARNING = MagicMock(side_effect=lambda x: x)
        mock_command.style.ERROR = MagicMock(side_effect=lambda x: x)
        mock_command.style.SQL_FIELD = MagicMock(side_effect=lambda x: x)
        mock_command.style.SUCCESS = MagicMock(side_effect=lambda x: x)

        # Mock file system
        mock_os_path_exists.return_value = True
        mock_os_listdir.return_value = ['test_file.json']
        
        # Sample JSON data
        sample_data = {
            "metadata": {
                "company": "TestCompany",
                "store_id": "123",
                "store_name": "Test Store"
            },
            "products": [
                {
                    "product_id_store": "prod1",
                    "name": "Product 1",
                    "category_path": ["Category A", "Subcategory A"]
                }
            ]
        }
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)

        # Mock database interactions
        mock_company = MagicMock()
        mock_store = MagicMock(name="Test Store", store_id="123")
        mock_category = MagicMock()
        mock_product = MagicMock()

        mock_get_or_create_company.return_value = (mock_company, True)
        mock_get_or_create_store.return_value = (mock_store, True)
        mock_get_or_create_category_hierarchy.return_value = mock_category
        mock_get_or_create_product.return_value = (mock_product, True)

        # Call the function
        update_products_from_processed(mock_command)

        # Assertions
        mock_os_path_exists.assert_called_once()
        mock_os_listdir.assert_called_once()
        mock_open_file.assert_called_once()
        mock_get_or_create_company.assert_called_once_with("TestCompany")
        mock_get_or_create_store.assert_called_once_with(company_obj=mock_company, division_obj=None, store_id="123", store_data=sample_data['metadata'])
        mock_atomic.assert_called_once()
        mock_get_or_create_category_hierarchy.assert_called_once_with(["Category A", "Subcategory A"], mock_company)
        mock_get_or_create_product.assert_called_once_with(sample_data['products'][0], mock_store, mock_category)
        mock_create_price.assert_called_once_with(sample_data['products'][0], mock_product, mock_store)
        mock_os_remove.assert_called_once()
        mock_command.stdout.write.assert_any_call('  Successfully processed products for test_file.json. Created: 1, Updated: 0, Failed: 0')
        mock_command.stdout.write.assert_any_call('\n--- Product update from processed data complete ---')
        mock_makedirs.assert_not_called() # No failed products
