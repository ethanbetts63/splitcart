import pytest
from django.db import IntegrityError
from companies.models import Category
from companies.tests.factories import CompanyFactory, CategoryFactory


@pytest.mark.django_db
class TestCategoryModel:
    def test_str_returns_name(self):
        category = CategoryFactory(name='Fruit & Veg')
        assert str(category) == 'Fruit & Veg'

    def test_unique_together_slug_company(self):
        company = CompanyFactory()
        Category.objects.create(name='Fruit', slug='fruit', company=company)
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Fruit Duplicate', slug='fruit', company=company)

    def test_same_slug_allowed_for_different_companies(self):
        company_a = CompanyFactory()
        company_b = CompanyFactory()
        CategoryFactory(slug='bakery', company=company_a)
        CategoryFactory(slug='bakery', company=company_b)  # should not raise

    def test_parents_many_to_many(self):
        parent = CategoryFactory()
        child = CategoryFactory()
        child.parents.add(parent)
        assert parent in child.parents.all()
        assert child in parent.subcategories.all()

    def test_primary_category_nullable(self):
        company = CompanyFactory()
        category = Category.objects.create(name='Uncategorised', slug='uncategorised', company=company)
        assert category.primary_category is None
