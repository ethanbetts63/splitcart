
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.utils.database_updating_utils.update_products_from_archive import update_products_from_archive

class UpdateProductsFromArchiveTest(TestCase):
    def setUp(self):
        self.mock_command = MagicMock()

    @patch('api.utils.database_updating_utils.update_products_from_archive.batch_create_category_relationships')
    @patch('api.utils.database_updating_utils.update_products_from_archive.batch_create_prices')
    @patch('api.utils.database_updating_utils.update_products_from_archive.batch_create_new_products')
    @patch('api.utils.database_updating_utils.update_products_from_archive.consolidate_product_data')
    def test_update_products_from_archive(self, mock_consolidate_product_data, mock_batch_create_new_products, mock_batch_create_prices, mock_batch_create_category_relationships):
        consolidated_data = {"product1": {}}
        mock_consolidate_product_data.return_value = consolidated_data
        product_cache = {"product1": MagicMock()}
        mock_batch_create_new_products.return_value = product_cache

        update_products_from_archive(self.mock_command)

        mock_consolidate_product_data.assert_called_once()
        mock_batch_create_new_products.assert_called_once_with(consolidated_data)
        mock_batch_create_prices.assert_called_once_with(consolidated_data, product_cache)
        mock_batch_create_category_relationships.assert_called_once_with(consolidated_data, product_cache)
        self.mock_command.stdout.write.assert_called_with(self.mock_command.style.SUCCESS("Fast update from archive complete."))
