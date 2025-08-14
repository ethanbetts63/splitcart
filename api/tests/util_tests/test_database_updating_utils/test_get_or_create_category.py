from django.test import TestCase
from companies.models import Category
from companies.tests.test_helpers.model_factories import CompanyFactory
from api.utils.database_updating_utils.get_or_create_category import get_or_create_category

class GetOrCreateCategoryTest(TestCase):

    def test_create_new_category(self):
        """Test that a new category is created if it doesn't exist."""
        company = CompanyFactory()
        category, created = get_or_create_category("New Category", company, "cat123")
        self.assertTrue(created)
        self.assertEqual(category.name, "New Category")
        self.assertEqual(category.slug, "new-category")
        self.assertEqual(category.company, company)
        self.assertEqual(category.store_category_id, "cat123")
        self.assertEqual(Category.objects.count(), 1)

    def test_get_existing_category(self):
        """Test that an existing category is retrieved."""
        company = CompanyFactory()
        Category.objects.create(name="Existing Category", slug="existing-category", company=company, store_category_id="old_id")
        category, created = get_or_create_category("Existing Category", company, "new_id")
        self.assertFalse(created)
        self.assertEqual(category.name, "Existing Category")
        self.assertEqual(category.slug, "existing-category")
        self.assertEqual(category.company, company)
        self.assertEqual(category.store_category_id, "old_id") # store_category_id should not be updated
        self.assertEqual(Category.objects.count(), 1)

    def test_get_existing_category_case_insensitive_name(self):
        """Test that an existing category is retrieved case-insensitively by name (due to slugification)."""
        company = CompanyFactory()
        Category.objects.create(name="CaseInsensitive", slug="caseinsensitive", company=company)
        category, created = get_or_create_category("caseinsensitive", company)
        self.assertFalse(created)
        self.assertEqual(category.name, "CaseInsensitive")
        self.assertEqual(category.slug, "caseinsensitive")
        self.assertEqual(Category.objects.count(), 1)

    def test_create_category_with_different_name_same_slug(self):
        """Test that a new category is not created if a different name results in the same slug."""
        company = CompanyFactory()
        Category.objects.create(name="Test Category", slug="test-category", company=company)
        category, created = get_or_create_category("Test-Category", company) # This should match the existing slug
        self.assertFalse(created)
        self.assertEqual(category.name, "Test Category") # Original name should be kept
        self.assertEqual(Category.objects.count(), 1)

    def test_store_category_id_on_creation(self):
        """Test that store_category_id is set correctly on creation."""
        company = CompanyFactory()
        category, created = get_or_create_category("Test ID Category", company, "specific_id_123")
        self.assertTrue(created)
        self.assertEqual(category.store_category_id, "specific_id_123")
