import pytest
from companies.tests.factories import PillarPageFactory, PrimaryCategoryFactory


@pytest.mark.django_db
class TestPillarPageModel:
    def test_str_returns_name(self):
        page = PillarPageFactory(name='Fresh Produce')
        assert str(page) == 'Fresh Produce'

    def test_can_add_primary_categories(self):
        page = PillarPageFactory()
        cat = PrimaryCategoryFactory()
        page.primary_categories.add(cat)
        assert cat in page.primary_categories.all()

    def test_primary_categories_accessible_from_category(self):
        page = PillarPageFactory()
        cat = PrimaryCategoryFactory()
        page.primary_categories.add(cat)
        assert page in cat.pillar_pages.all()
