from django.test import TestCase
from companies.models import Category
from companies.tests.test_helpers.model_factories import CompanyFactory
from api.utils.database_updating_utils.get_or_create_category_hierarchy import get_or_create_category_hierarchy

class GetOrCreateCategoryHierarchyTest(TestCase):

    def test_create_simple_hierarchy(self):
        """Test creating a simple two-level category hierarchy."""
        company = CompanyFactory()
        category_path = ["Fresh Food", "Fruit & Vegetables"]
        
        final_category = get_or_create_category_hierarchy(category_path, company)
        
        self.assertIsNotNone(final_category)
        self.assertEqual(final_category.name, "Fruit & Vegetables")
        self.assertEqual(Category.objects.count(), 2) # Both Fresh Food and Fruit & Vegetables
        
        fresh_food = Category.objects.get(name="Fresh Food", company=company)
        fruit_veg = Category.objects.get(name="Fruit & Vegetables", company=company)
        
        self.assertIn(fresh_food, fruit_veg.parents.all())

    def test_create_multi_level_hierarchy(self):
        """Test creating a multi-level category hierarchy."""
        company = CompanyFactory()
        category_path = ["Pantry", "Pasta & Sauces", "Pasta"]
        
        final_category = get_or_create_category_hierarchy(category_path, company)
        
        self.assertIsNotNone(final_category)
        self.assertEqual(final_category.name, "Pasta")
        self.assertEqual(Category.objects.count(), 3)
        
        pantry = Category.objects.get(name="Pantry", company=company)
        pasta_sauces = Category.objects.get(name="Pasta & Sauces", company=company)
        pasta = Category.objects.get(name="Pasta", company=company)
        
        self.assertIn(pantry, pasta_sauces.parents.all())
        self.assertIn(pasta_sauces, pasta.parents.all())

    def test_existing_categories_are_reused(self):
        """Test that existing categories are reused and relationships are updated."""
        company = CompanyFactory()
        # Create part of the hierarchy beforehand
        fresh_food_existing = Category.objects.create(name="Fresh Food", slug="fresh-food", company=company)
        
        category_path = ["Fresh Food", "Fruit & Vegetables"]
        final_category = get_or_create_category_hierarchy(category_path, company)
        
        self.assertIsNotNone(final_category)
        self.assertEqual(final_category.name, "Fruit & Vegetables")
        self.assertEqual(Category.objects.count(), 2) # Only Fruit & Vegetables was created
        
        fresh_food_retrieved = Category.objects.get(name="Fresh Food", company=company)
        self.assertEqual(fresh_food_existing.id, fresh_food_retrieved.id) # Ensure it's the same object
        
        fruit_veg = Category.objects.get(name="Fruit & Vegetables", company=company)
        self.assertIn(fresh_food_retrieved, fruit_veg.parents.all())

    def test_single_level_category(self):
        """Test creating a single-level category."""
        company = CompanyFactory()
        category_path = ["Dairy"]
        
        final_category = get_or_create_category_hierarchy(category_path, company)
        
        self.assertIsNotNone(final_category)
        self.assertEqual(final_category.name, "Dairy")
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(final_category.parents.count(), 0)

    def test_empty_category_path(self):
        """Test that an empty category path returns None."""
        company = CompanyFactory()
        category_path = []
        
        final_category = get_or_create_category_hierarchy(category_path, company)
        
        self.assertIsNone(final_category)
        self.assertEqual(Category.objects.count(), 0)
