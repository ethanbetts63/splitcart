from django.test import TestCase
from django.db.utils import IntegrityError
from companies.models import Category
from companies.tests.test_helpers.model_factories import CategoryFactory, CompanyFactory

class CategoryModelTest(TestCase):

    def test_category_creation(self):
        """Test that a category can be created."""
        category = CategoryFactory()
        self.assertIsNotNone(category.id)
        self.assertIsNotNone(category.name)
        self.assertIsNotNone(category.slug)
        self.assertIsNotNone(category.company)

    def test_category_str_representation(self):
        """Test the string representation of the category."""
        category = CategoryFactory(name="Test Category")
        self.assertEqual(str(category), "Test Category")

    def test_unique_together_constraint(self):
        """Test that slug and company are unique together."""
        company = CompanyFactory()
        slug = "test-slug"
        CategoryFactory(slug=slug, company=company)
        with self.assertRaises(IntegrityError):
            CategoryFactory(slug=slug, company=company)

    def test_parents_relationship(self):
        """Test the parents many-to-many relationship."""
        parent1 = CategoryFactory()
        parent2 = CategoryFactory()
        child = CategoryFactory()
        child.parents.add(parent1, parent2)
        self.assertEqual(child.parents.count(), 2)
        self.assertIn(parent1, child.parents.all())
        self.assertIn(parent2, child.parents.all())

    def test_nullable_and_blankable_fields(self):
        """Test that nullable and blankable fields are handled correctly."""
        category = CategoryFactory(store_category_id=None)
        self.assertIsNone(category.store_category_id)
        
        # Test that parents can be blank
        category_with_no_parents = CategoryFactory()
        self.assertEqual(category_with_no_parents.parents.count(), 0)