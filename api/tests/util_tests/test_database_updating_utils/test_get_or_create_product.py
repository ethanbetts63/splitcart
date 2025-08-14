from django.test import TestCase
from unittest.mock import patch, Mock
from products.models import Product, Price
from companies.models import Store, Category
from companies.tests.test_helpers.model_factories import StoreFactory, CategoryFactory
from products.tests.test_helpers.model_factories import ProductFactory, PriceFactory
from api.utils.database_updating_utils.get_or_create_product import get_or_create_product

class GetOrCreateProductTest(TestCase):

    def setUp(self):
        self.store = StoreFactory()
        self.category = CategoryFactory()

    def test_create_new_product_no_match(self):
        """Test that a new product is created if no match is found."""
        product_data = {
            'name': 'New Product',
            'brand': 'New Brand',
            'package_size': '100g',
            'barcode': '1234567890123',
            'image_url_main': 'http://example.com/image.jpg',
            'description_long': 'Long description',
            'country_of_origin': 'Australia',
            'ingredients': 'Ingredients list'
        }
        product, created = get_or_create_product(product_data, self.store, self.category)
        self.assertTrue(created)
        self.assertIsNotNone(product.id)
        self.assertEqual(product.name, 'New Product')
        self.assertEqual(product.brand, 'New Brand')
        self.assertEqual(product.size, '100g')
        self.assertEqual(product.barcode, '1234567890123')
        self.assertEqual(product.image_url, 'http://example.com/image.jpg')
        self.assertEqual(product.description, 'Long description')
        self.assertEqual(product.country_of_origin, 'Australia')
        self.assertEqual(product.ingredients, 'Ingredients list')
        self.assertIn(self.category, product.category.all())

    def test_get_existing_product_by_barcode(self):
        """Test that an existing product is returned if its barcode matches."""
        existing_product = ProductFactory(barcode='BARCODE123')
        product_data = {'barcode': 'BARCODE123', 'name': 'Different Name'}
        product, created = get_or_create_product(product_data, self.store, self.category)
        self.assertFalse(created)
        self.assertEqual(product, existing_product)
        self.assertIn(self.category, product.category.all())

    @patch('products.models.Price.objects.filter')
    def test_get_existing_product_by_store_product_id(self, mock_price_filter):
        """Test that an existing product is returned if its store_product_id matches a Price record."""
        existing_product = ProductFactory()
        mock_price = Mock(product=existing_product)
        mock_price_filter.return_value.latest.return_value = mock_price

        product_data = {'store_product_id': 'SPID123'}
        product, created = get_or_create_product(product_data, self.store, self.category)
        self.assertFalse(created)
        self.assertEqual(product, existing_product)
        mock_price_filter.assert_called_with(store=self.store, store_product_id='SPID123', is_active=True)
        self.assertIn(self.category, product.category.all())

    def test_get_existing_product_by_normalized_name_brand_size(self):
        """Test that an existing product is returned by normalized name, brand, and size."""
        existing_product = ProductFactory(name='Test Product', brand='Test Brand', size='100g')
        product_data = {'name': 'test product', 'brand': 'test brand', 'package_size': '100G'}
        product, created = get_or_create_product(product_data, self.store, self.category)
        self.assertFalse(created)
        self.assertEqual(product, existing_product)
        self.assertIn(self.category, product.category.all())

    def test_category_always_associated(self):
        """Test that the category is always associated, whether product is created or found."""
        # Test with new product
        product_data_new = {'name': 'New Product 2', 'brand': 'Brand 2', 'package_size': '200g'}
        product_new, created_new = get_or_create_product(product_data_new, self.store, self.category)
        self.assertTrue(created_new)
        self.assertIn(self.category, product_new.category.all())

        # Test with existing product (by barcode)
        existing_product_barcode = ProductFactory(barcode='BARCODE456')
        product_data_existing_barcode = {'barcode': 'BARCODE456'}
        product_existing_barcode, created_existing_barcode = get_or_create_product(product_data_existing_barcode, self.store, self.category)
        self.assertFalse(created_existing_barcode)
        self.assertIn(self.category, product_existing_barcode.category.all())

        # Test with existing product (by name/brand/size)
        existing_product_name = ProductFactory(name='Existing Name', brand='Existing Brand', size='300g')
        product_data_existing_name = {'name': 'Existing Name', 'brand': 'Existing Brand', 'package_size': '300g'}
        product_existing_name, created_existing_name = get_or_create_product(product_data_existing_name, self.store, self.category)
        self.assertFalse(created_existing_name)
        self.assertIn(self.category, product_existing_name.category.all())
