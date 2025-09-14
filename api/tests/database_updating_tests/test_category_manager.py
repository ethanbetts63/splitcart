from django.test import TestCase
from unittest.mock import Mock, patch

from api.database_updating_classes.category_manager import CategoryManager
from companies.models import Company, Category
from products.models import Product

from companies.tests.test_helpers.model_factories import CompanyFactory, CategoryFactory

class CategoryManagerTests(TestCase):

    def setUp(self):
        self.mock_command = Mock()
        self.company = CompanyFactory(name="Test Company")
        # Instantiate the manager. It will have an empty cache as no categories exist yet.
        self.manager = CategoryManager(self.mock_command)

    def test_collect_all_paths(self):
        """Test that unique category paths are collected correctly from consolidated data."""
        # FIX: The key is 'product', not 'product_details'
        consolidated_data = {
            'item-a-1l': {'product': {'category_path': ['Bakery', 'Bread']}},
            'item-b-500g': {'product': {'category_path': ['Bakery', 'Rolls']}},
            'item-c-2l': {'product': {'category_path': ['Bakery', 'Bread']}}, # Duplicate path
            'item-d-1kg': {'product': {}}, # No path
            'item-e-ea': {'product': {'category_path': ['Fruit & Veg', 'Fruit', 'Apples']}},
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
        existing_cat = CategoryFactory(name='Bakery', company=self.company)
        # FIX: The cache key is now a tuple of (name, company_id)
        self.manager.category_cache = {(existing_cat.name, self.company.id): existing_cat}
        
        all_paths = {
            ('Bakery', 'Bread'),
            ('Fruit & Veg', 'Apples'),
        }
        
        mock_bulk_create.return_value = [
            Category(name='Bread', company=self.company),
            Category(name='Fruit & Veg', company=self.company),
            Category(name='Apples', company=self.company),
        ]

        # Act
        # FIX: The method now requires the company object
        self.manager._create_new_categories(all_paths, self.company)

        # Assert
        mock_bulk_create.assert_called_once()
        
        call_args = mock_bulk_create.call_args[0][0]
        created_names = {cat.name for cat in call_args}
        self.assertEqual(created_names, {'Bread', 'Fruit & Veg', 'Apples'})

        # FIX: Check the cache with the correct tuple key
        self.assertIn(('Bread', self.company.id), self.manager.category_cache)
        self.assertIn(('Fruit & Veg', self.company.id), self.manager.category_cache)
        self.assertIn(('Apples', self.company.id), self.manager.category_cache)
        self.assertIn(('Bakery', self.company.id), self.manager.category_cache)

    @patch('api.database_updating_classes.category_manager.Category.parents.through.objects.bulk_create')
    def test_create_parent_child_links(self, mock_bulk_create):
        """Test that parent-child relationship links are created."""
        # Arrange
        cat1 = CategoryFactory(id=1, name='Bakery', company=self.company)
        cat2 = CategoryFactory(id=2, name='Bread', company=self.company)
        cat3 = CategoryFactory(id=3, name='Rolls', company=self.company)
        # FIX: The cache key is now a tuple of (name, company_id)
        self.manager.category_cache = {
            (cat1.name, self.company.id): cat1,
            (cat2.name, self.company.id): cat2,
            (cat3.name, self.company.id): cat3,
        }

        all_paths = {
            ('Bakery', 'Bread'),
            ('Bakery', 'Rolls'),
        }

        # Act
        # FIX: The method now requires the company object
        self.manager._create_parent_child_links(all_paths, self.company)

        # Assert
        mock_bulk_create.assert_called_once()
        call_args = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(call_args), 2)
        created_links = {(link.from_category_id, link.to_category_id) for link in call_args}
        expected_links = {(cat1.id, cat2.id), (cat1.id, cat3.id)}
        self.assertEqual(created_links, expected_links)

    @patch('api.database_updating_classes.category_manager.Product.category.through.objects.bulk_create')
    def test_link_products_to_categories(self, mock_bulk_create):
        """Test that products are correctly linked to their leaf categories."""
        # Arrange
        prod1 = Product(id=101)
        prod2 = Product(id=102)
        cat_bread = CategoryFactory(id=201, name='Bread', company=self.company)
        cat_rolls = CategoryFactory(id=202, name='Rolls', company=self.company)

        # FIX: The cache key is now a tuple of (name, company_id)
        self.manager.category_cache = {
            (cat_bread.name, self.company.id): cat_bread,
            (cat_rolls.name, self.company.id): cat_rolls,
        }
        product_cache = {
            'item-a-1l': prod1,
            'item-b-500g': prod2,
        }
        # FIX: The key is 'category_path', not 'category_paths'
        consolidated_data = {
            'item-a-1l': {'product': {'category_path': ['Bakery', 'Bread']}},
            'item-b-500g': {'product': {'category_path': ['Bakery', 'Rolls']}},
        }

        # Act
        # FIX: The method now requires the company object
        self.manager._link_products_to_categories(consolidated_data, product_cache, self.company)

        # Assert
        mock_bulk_create.assert_called_once()
        call_args = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(call_args), 2)

        created_links = {(link.product_id, link.category_id) for link in call_args}
        expected_links = {(prod1.id, cat_bread.id), (prod2.id, cat_rolls.id)}
        self.assertEqual(created_links, expected_links)
