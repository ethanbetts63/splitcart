import pytest
from data_management.serializers.pillar_page_serializer import PillarPageSerializer
from companies.tests.factories import PillarPageFactory, PrimaryCategoryFactory


@pytest.mark.django_db
class TestPillarPageSerializer:
    def test_contains_expected_fields(self):
        page = PillarPageFactory()
        serializer = PillarPageSerializer(page)
        assert set(serializer.data.keys()) == {
            'name', 'slug', 'hero_title', 'introduction_paragraph', 'primary_categories'
        }

    def test_name_field_value(self):
        page = PillarPageFactory(name='Dairy & Eggs')
        serializer = PillarPageSerializer(page)
        assert serializer.data['name'] == 'Dairy & Eggs'

    def test_slug_field_value(self):
        page = PillarPageFactory(slug='dairy-eggs')
        serializer = PillarPageSerializer(page)
        assert serializer.data['slug'] == 'dairy-eggs'

    def test_hero_title_field_value(self):
        page = PillarPageFactory(hero_title='Find the Best Dairy Prices')
        serializer = PillarPageSerializer(page)
        assert serializer.data['hero_title'] == 'Find the Best Dairy Prices'

    def test_introduction_paragraph_field_value(self):
        page = PillarPageFactory(introduction_paragraph='Compare dairy prices across stores.')
        serializer = PillarPageSerializer(page)
        assert serializer.data['introduction_paragraph'] == 'Compare dairy prices across stores.'

    def test_primary_categories_empty_when_none_linked(self):
        page = PillarPageFactory()
        serializer = PillarPageSerializer(page)
        assert serializer.data['primary_categories'] == []

    def test_primary_categories_serialized_when_linked(self):
        page = PillarPageFactory()
        cat1 = PrimaryCategoryFactory(name='Milk')
        cat2 = PrimaryCategoryFactory(name='Cheese')
        page.primary_categories.set([cat1, cat2])
        serializer = PillarPageSerializer(page)
        names = {c['name'] for c in serializer.data['primary_categories']}
        assert names == {'Milk', 'Cheese'}

    def test_primary_categories_contain_expected_fields(self):
        page = PillarPageFactory()
        cat = PrimaryCategoryFactory()
        page.primary_categories.set([cat])
        serializer = PillarPageSerializer(page)
        assert set(serializer.data['primary_categories'][0].keys()) == {
            'name', 'slug', 'price_comparison_data'
        }
