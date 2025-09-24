from django.test import TestCase
from unittest.mock import Mock, patch

from data_management.database_updating_classes.update_orchestrator import UpdateOrchestrator
from products.models import Product
from products.tests.test_helpers.model_factories import ProductFactory
from companies.tests.test_helpers.model_factories import StoreFactory

class UpdateOrchestratorLogicTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.orchestrator = UpdateOrchestrator(self.mock_command, inbox_path='/tmp/inbox')

    def test_enrich_existing_product(self):
        """Test that the enrichment logic within _process_consolidated_data works correctly."""
        # 1. Arrange
        # An existing product with some missing data and an old description
        existing_product = ProductFactory(
            size='100g',
            barcode=None, 
            url=None, 
            description='a long existing description'
        )

        # New data from a scrape with a new barcode, a new url, and a shorter description
        product_details = {
            'barcode': '1234567890123',
            'url': 'http://new.url/product',
            'description_long': 'a short new desc',
            'price_current': 9.99 # Needed for add_price
        }
        consolidated_data = {
            existing_product.normalized_name_brand_size: {
                'product': product_details,
                'metadata': {'company': 'coles'}
            }
        }

        # Mock the dependencies for _process_consolidated_data
        mock_resolver = Mock()
        mock_resolver.find_match.return_value = existing_product
        mock_uow = Mock()
        mock_variation_manager = Mock()
        mock_brand_manager = Mock()
        mock_store_obj = StoreFactory()

        # 2. Act
        self.orchestrator._process_consolidated_data(
            consolidated_data, 
            mock_resolver, 
            mock_uow, 
            mock_variation_manager, 
            mock_brand_manager,
            mock_store_obj
        )

        # 3. Assert
        # Check that the product object was updated in memory
        self.assertEqual(existing_product.barcode, '1234567890123')
        self.assertEqual(existing_product.url, 'http://new.url/product')
        # Description should be updated because the new one is shorter
        self.assertEqual(existing_product.description, 'a short new desc')

        # Check that the collaborators were called correctly
        mock_variation_manager.check_for_variation.assert_called_once_with(
            product_details, existing_product, 'coles'
        )
        mock_uow.add_for_update.assert_called_once_with(existing_product)
        mock_uow.add_price.assert_called_once_with(existing_product, mock_store_obj, product_details)

    def test_enrich_merges_sizes(self):
        """Test that the enrichment logic correctly merges the sizes list."""
        # 1. Arrange
        existing_product = ProductFactory(sizes=['500g'])
        product_details = {
            'sizes': ['1kg', '500g'],
            'price_current': 9.99 # Needed for add_price
        }
        consolidated_data = {
            existing_product.normalized_name_brand_size: {
                'product': product_details,
                'metadata': {'company': 'coles'}
            }
        }

        mock_resolver = Mock()
        mock_resolver.find_match.return_value = existing_product
        mock_uow = Mock()
        mock_variation_manager = Mock()
        mock_brand_manager = Mock()
        mock_store_obj = StoreFactory()

        # 2. Act
        self.orchestrator._process_consolidated_data(
            consolidated_data, 
            mock_resolver, 
            mock_uow, 
            mock_variation_manager, 
            mock_brand_manager,
            mock_store_obj
        )

        # 3. Assert
        # Check that the product's sizes list was updated and sorted
        self.assertEqual(existing_product.sizes, ['1kg', '500g'])

        # Check that the product was marked for update
        mock_uow.add_for_update.assert_called_once_with(existing_product)
