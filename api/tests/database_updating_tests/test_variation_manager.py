from django.test import TestCase
from unittest.mock import Mock

from api.database_updating_classes.variation_manager import VariationManager
from products.models import Product, Price, ProductBrand
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory, ProductBrandFactory

class VariationManagerTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.mock_uow = Mock()
        self.manager = VariationManager(self.mock_command, self.mock_uow)

    def test_check_for_variation_no_change_for_identical_names(self):
        """Test that nothing happens if the incoming and existing names are the same."""
        existing_product = ProductFactory(name='Test Product', barcode='123')
        incoming_details = {'name': 'Test Product'}

        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        self.mock_uow.add_for_update.assert_not_called()

    def test_check_for_variation_no_change_if_no_barcode(self):
        """Test that no variation is recorded if the existing product has no barcode."""
        existing_product = ProductFactory(name='Test Product', barcode=None)
        incoming_details = {'name': 'A Different Name'}

        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        self.mock_uow.add_for_update.assert_not_called()

    def test_check_for_new_variation(self):
        """Test that a new variation is correctly identified and processed."""
        existing_product = ProductFactory(
            name='Canonical Product', 
            barcode='12345', 
            name_variations=[],
            normalized_name_brand_size_variations=[],
            normalized_name_brand_size='canonical-product-normalized-string'
        )

        incoming_details = {
            'name': 'A New Variation Name',
            'normalized_name_brand_size': 'new-variation-normalized'
        }

        # Act
        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        # Assert
        # 1. Product object is updated in memory
        self.assertIn(['A New Variation Name', 'coles'], existing_product.name_variations)
        self.assertIn('new-variation-normalized', existing_product.normalized_name_brand_size_variations)

        # 2. Unit of Work is notified
        self.mock_uow.add_for_update.assert_called_with(existing_product)

    def test_check_for_new_brand_variation(self):
        """Test that a new brand variation is correctly added."""
        brand = ProductBrandFactory(name='Canonical Brand', normalized_name='canonical-brand', name_variations=[])
        existing_product = ProductFactory(brand=brand, barcode='123')
        incoming_details = {
            'brand': 'A New Brand Name',
            'normalized_brand': 'a-new-brand-name'
        }

        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        self.assertIn('A New Brand Name', brand.name_variations)
        self.mock_uow.add_for_update.assert_called_with(brand)

    def test_check_for_variation_deduplicates_variations(self):
        """Test that the same variation is not added twice."""
        existing_product = ProductFactory(
            name='Canonical Product', 
            barcode='12345',
            name_variations=[['Existing Variation', 'coles']],
            normalized_name_brand_size_variations=['existing-normalized']
        )
        incoming_details = {
            'name': 'Existing Variation',
            'normalized_name_brand_size': 'existing-normalized'
        }

        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        # Assert that the lists have not grown
        self.assertEqual(len(existing_product.name_variations), 1)
        self.assertEqual(len(existing_product.normalized_name_brand_size_variations), 1)
        # Assert that UoW was not called as no update was made
        self.mock_uow.add_for_update.assert_not_called()