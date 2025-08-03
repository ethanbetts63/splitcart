from django.test import TestCase
from django.db.utils import IntegrityError
from companies.tests.test_helpers.model_factories import CategoryFactory, StoreFactory

class CategoryModelTest(TestCase):

    def test_category_creation(self):
        category = CategoryFactory()
        self.assertIsNotNone(category.id)
        self.assertIsNotNone(category.name)
        self.assertIsNotNone(category.slug)

    def test_category_str_representation(self):
        parent = CategoryFactory(name="Parent")
        child = CategoryFactory(name="Child", parent=parent)
        grandchild = CategoryFactory(name="Grandchild", parent=child)
        self.assertEqual(str(grandchild), "Parent > Child > Grandchild")

    def test_unique_together_constraint(self):
        parent = CategoryFactory(name="UniqueParent")
        CategoryFactory(name="UniqueChild", parent=parent)
        with self.assertRaises(IntegrityError):
            CategoryFactory(name="UniqueChild", parent=parent)

    def test_toplevel_category_unique_name(self):
        CategoryFactory(name="TopLevel", parent=None)
        with self.assertRaises(IntegrityError):
            CategoryFactory(name="TopLevel", parent=None)

    def test_nullable_fields(self):
        category = CategoryFactory(store_category_id=None, parent=None, store=None)
        self.assertIsNone(category.store_category_id)
        self.assertIsNone(category.parent)
        self.assertIsNone(category.store)
