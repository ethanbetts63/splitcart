from django.test import TestCase
from unittest.mock import Mock
from companies.models import Category
from companies.tests.test_helpers.model_factories import CompanyFactory
from products.tests.test_helpers.model_factories import ProductFactory
from api.utils.database_updating_utils.batch_create_category_relationships import batch_create_category_relationships

class TestBatchCreateCategoryRelationships(TestCase):

    def setUp(self):
        self.company = CompanyFactory(name="Test Company")
        self.product = ProductFactory()

        self.product_cache = {
            "key1": self.product
        }

        self.consolidated_data = {
            "key1": {
                "company_name": "Test Company",
                "category_paths": [
                    ["Bakery", "Bread", "Rolls"]
                ]
            }
        }

        self.mock_command = Mock()
        self.mock_command.stdout = Mock()
        self.mock_command.style = Mock()

    def test_batch_create_category_relationships_success(self):
        batch_create_category_relationships(self.consolidated_data, self.product_cache)

        # Part A: Assert categories exist
        self.assertEqual(Category.objects.count(), 3)
        bakery = Category.objects.get(name="Bakery")
        bread = Category.objects.get(name="Bread")
        rolls = Category.objects.get(name="Rolls")
        self.assertEqual(bakery.company, self.company)
        self.assertEqual(bread.company, self.company)
        self.assertEqual(rolls.company, self.company)

        # Part B: Assert parent-child relationships
        self.assertIn(bakery, bread.parents.all())
        self.assertIn(bread, rolls.parents.all())

        # Part C: Assert product-category relationship
        self.assertIn(rolls, self.product.category.all())
