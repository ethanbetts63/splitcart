import pytest
from django.db import IntegrityError
from companies.models import CategoryLink
from companies.tests.factories import CategoryFactory, CategoryLinkFactory


@pytest.mark.django_db
class TestCategoryLinkModel:
    def test_str_contains_both_category_names(self):
        cat_a = CategoryFactory(name='Bakery')
        cat_b = CategoryFactory(name='Bread')
        link = CategoryLinkFactory(category_a=cat_a, category_b=cat_b, link_type=CategoryLink.LinkType.MATCH)
        result = str(link)
        assert 'Bakery' in result
        assert 'Bread' in result

    def test_str_contains_link_type_display(self):
        link = CategoryLinkFactory(link_type=CategoryLink.LinkType.MATCH)
        assert 'Match' in str(link)

    def test_link_type_close_relation_display(self):
        cat_a = CategoryFactory()
        cat_b = CategoryFactory()
        link = CategoryLink.objects.create(
            category_a=cat_a, category_b=cat_b, link_type=CategoryLink.LinkType.CLOSE_RELATION
        )
        assert link.get_link_type_display() == 'Close Relation'

    def test_link_type_distant_relation_display(self):
        cat_a = CategoryFactory()
        cat_b = CategoryFactory()
        link = CategoryLink.objects.create(
            category_a=cat_a, category_b=cat_b, link_type=CategoryLink.LinkType.DISTANT_RELATION
        )
        assert link.get_link_type_display() == 'Distant Relation'

    def test_duplicate_link_raises_integrity_error(self):
        cat_a = CategoryFactory()
        cat_b = CategoryFactory()
        CategoryLink.objects.create(category_a=cat_a, category_b=cat_b, link_type=CategoryLink.LinkType.MATCH)
        with pytest.raises(IntegrityError):
            CategoryLink.objects.create(
                category_a=cat_a, category_b=cat_b, link_type=CategoryLink.LinkType.CLOSE_RELATION
            )
