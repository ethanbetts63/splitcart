import pytest
from django.db import IntegrityError
from companies.models import PrimaryCategory
from companies.tests.factories import PrimaryCategoryFactory


@pytest.mark.django_db
class TestPrimaryCategoryModel:
    def test_str_returns_name(self):
        category = PrimaryCategoryFactory(name='Fruit')
        assert str(category) == 'Fruit'

    def test_save_auto_generates_slug_from_name(self):
        category = PrimaryCategory.objects.create(name='Dairy And Eggs')
        assert category.slug == 'dairy-and-eggs'

    def test_save_does_not_overwrite_provided_slug(self):
        category = PrimaryCategory.objects.create(name='Fruit', slug='custom-slug')
        assert category.slug == 'custom-slug'

    def test_name_uniqueness_enforced(self):
        PrimaryCategory.objects.create(name='Bakery', slug='bakery')
        with pytest.raises(IntegrityError):
            PrimaryCategory.objects.create(name='Bakery', slug='bakery-2')

    def test_price_comparison_data_defaults_to_dict(self):
        category = PrimaryCategoryFactory()
        assert category.price_comparison_data == {}

    def test_sub_categories_many_to_many(self):
        parent = PrimaryCategoryFactory(name='Food')
        child = PrimaryCategoryFactory(name='Fruit')
        parent.sub_categories.add(child)
        assert child in parent.sub_categories.all()
        assert parent in child.parent_categories.all()
