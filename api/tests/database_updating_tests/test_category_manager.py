from django.test import TestCase
from unittest.mock import Mock, patch

from api.database_updating_classes.category_manager import CategoryManager
from companies.models import Company, Category
from products.models import Product

from companies.tests.test_helpers.model_factories import CompanyFactory, CategoryFactory
from products.tests.test_helpers.model_factories import ProductFactory

class CategoryManagerTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.company = CompanyFactory(name="Test Company")
        # Instantiate the manager. It will have an empty cache as no categories exist yet.
        self.manager = CategoryManager(self.mock_command)

    def test_collect_all_paths(self):
        """Test that unique category paths are collected correctly from consolidated data."""
        consolidated_data = {
            'item-a-1l': {'product_details': {'category_path': ['Bakery', 'Bread']}},
            'item-b-500g': {'product_details': {'category_path': ['Bakery', 'Rolls']}},
            'item-c-2l': {'product_details': {'category_path': ['Bakery', 'Bread']}}, # Duplicate path
            'item-d-1kg': {'product_details': {}}, # No path
            'item-e-ea': {'product_details': {'category_path': ['Fruit & Veg', 'Fruit', 'Apples']}},
        }

        expected_paths = {
            ('Bakery', 'Bread'),
            ('Bakery', 'Rolls'),
            ('Fruit & Veg', 'Fruit', 'Apples'),
        }

        result = self.manager._collect_all_paths(consolidated_data)
        self.assertEqual(result, expected_paths)

    @patch('api.database_updating_classes.category_manager.Category.objects.bulk_create')
    def test_create_new_categories(self, mock_bulk_create):
        """Test that new categories are created and the cache is updated."""
        # Arrange
        # Pre-load the cache with one existing category
        existing_cat = CategoryFactory(name='Bakery', company=self.company)
        self.manager.category_cache = {'Bakery': existing_cat}
        
        all_paths = {
            ('Bakery', 'Bread'),
            ('Fruit & Veg', 'Apples'),
        }
        
        # Mock the return value of bulk_create to simulate new categories being created
        # The real bulk_create returns a list of the created objects
        mock_bulk_create.return_value = [
            Category(name='Bread', company=self.company),
            Category(name='Fruit & Veg', company=self.company),
            Category(name='Apples', company=self.company),
        ]

        # Act
        self.manager._create_new_categories(all_paths, self.company)

        # Assert
        mock_bulk_create.assert_called_once()
        
        # Check the call arguments - we expect 'Bread', 'Fruit & Veg', and 'Apples' to be created
        call_args = mock_bulk_create.call_args[0][0]
        created_names = {cat.name for cat in call_args}
        self.assertEqual(created_names, {'Bread', 'Fruit & Veg', 'Apples'})

        # Check that the internal cache was updated
        self.assertIn('Bread', self.manager.category_cache)
        self.assertIn('Fruit & Veg', self.manager.category_cache)
        self.assertIn('Apples', self.manager.category_cache)
        self.assertIn('Bakery', self.manager.category_cache) # Ensure the original is still there

    @patch('api.database_updating_classes.category_manager.Category.parents.through.objects.bulk_create')
    def test_create_parent_child_links(self, mock_bulk_create):
        """Test that parent-child relationship links are created."""
        # Arrange
        cat1 = CategoryFactory(id=1, name='Bakery')
        cat2 = CategoryFactory(id=2, name='Bread')
        cat3 = CategoryFactory(id=3, name='Rolls')
        self.manager.category_cache = {'Bakery': cat1, 'Bread': cat2, 'Rolls': cat3}

        all_paths = {
            ('Bakery', 'Bread'),
            ('Bakery', 'Rolls'),
        }

        # Act
        self.manager._create_parent_child_links(all_paths)

        # Assert
        mock_bulk_create.assert_called_once()
        call_args = mock_bulk_create.call_args[0][0]
        
        # We expect two links to be created
        self.assertEqual(len(call_args), 2)

        # Check that the links are correct (order might not be guaranteed)
        created_links = {(link.from_category_id, link.to_category_id) for link in call_args}
        expected_links = {(cat1.id, cat2.id), (cat1.id, cat3.id)}
        self.assertEqual(created_links, expected_links)

    @patch('api.database_updating_classes.category_manager.Product.category.through.objects.bulk_create')
    def test_link_products_to_categories(self, mock_bulk_create):
        """Test that products are correctly linked to their leaf categories."""
        # Arrange
        prod1 = ProductFactory(id=101)
        prod2 = ProductFactory(id=102)
        cat_bread = CategoryFactory(id=201, name='Bread')
        cat_rolls = CategoryFactory(id=202, name='Rolls')

        self.manager.category_cache = {'Bread': cat_bread, 'Rolls': cat_rolls}
        product_cache = {
            'item-a-1l': prod1,
            'item-b-500g': prod2,
        }
        consolidated_data = {
            'item-a-1l': {'product': {'category_paths': [['Bakery', 'Bread']]}},
            'item-b-500g': {'product': {'category_paths': [['Bakery', 'Rolls']]}},
        }

        # Act
        self.manager._link_products_to_categories(consolidated_data, product_cache)

        # Assert
        mock_bulk_create.assert_called_once()
        call_args = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(call_args), 2)

        created_links = {(link.product_id, link.category_id) for link in call_args}
        expected_links = {(prod1.id, cat_bread.id), (prod2.id, cat_rolls.id)}
        self.assertEqual(created_links, expected_links)