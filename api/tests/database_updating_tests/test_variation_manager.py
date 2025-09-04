from django.test import TestCase
from unittest.mock import Mock

from api.database_updating_classes.variation_manager import VariationManager
from products.models import Product, Price
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory

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
        self.assertEqual(len(self.manager.new_hotlist_entries), 0)

    def test_check_for_variation_no_change_if_no_barcode(self):
        """Test that no variation is recorded if the existing product has no barcode."""
        existing_product = ProductFactory(name='Test Product', barcode=None)
        incoming_details = {'name': 'A Different Name'}

        self.manager.check_for_variation(incoming_details, existing_product, 'coles')

        self.mock_uow.add_for_update.assert_not_called()
        self.assertEqual(len(self.manager.new_hotlist_entries), 0)

    def test_check_for_new_variation(self):
        """Test that a new variation is correctly identified and processed."""
        existing_product = ProductFactory(
            name='Canonical Product', 
            barcode='12345', 
            name_variations=[],
            normalized_name_brand_size_variations=[]
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
        self.mock_uow.add_for_update.assert_called_once_with(existing_product)

        # 3. Hotlist is updated
        self.assertEqual(len(self.manager.new_hotlist_entries), 1)
        hotlist_entry = self.manager.new_hotlist_entries[0]
        self.assertEqual(hotlist_entry['new_variation'], 'A New Variation Name')
        self.assertEqual(hotlist_entry['canonical_name'], 'Canonical Product')
        self.assertEqual(hotlist_entry['barcode'], '12345')

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

    def test_reconcile_duplicates_merges_products(self):
        """Test that a duplicate product is correctly merged into the canonical one."""
        # 1. Arrange
        canonical_product = ProductFactory(name='Canonical Product', barcode='123')
        duplicate_product = ProductFactory(name='Duplicate Product Name', barcode=None) # No barcode conflict
        
        # Give the duplicate product a price record
        price_to_move = PriceFactory(product=duplicate_product)
        self.assertEqual(Price.objects.filter(product=canonical_product).count(), 0)

        # Manually populate the hotlist to simulate a variation having been found
        self.manager.new_hotlist_entries = [{
            'new_variation': 'Duplicate Product Name',
            'canonical_name': 'Canonical Product',
            'barcode': '123'
        }]

        # 2. Act
        self.manager.reconcile_duplicates()

        # 3. Assert
        # Price record should have been moved
        self.assertEqual(Price.objects.filter(product=duplicate_product).count(), 0)
        self.assertEqual(Price.objects.filter(product=canonical_product).count(), 1)
        price_to_move.refresh_from_db()
        self.assertEqual(price_to_move.product, canonical_product)

        # Duplicate product should have been deleted
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=duplicate_product.id)

        # Hotlist should be cleared
        self.assertEqual(len(self.manager.new_hotlist_entries), 0)