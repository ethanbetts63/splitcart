import pytest
from companies.serializers.primary_category_serializer import PrimaryCategorySerializer
from companies.tests.factories import PrimaryCategoryFactory


@pytest.mark.django_db
class TestPrimaryCategorySerializer:
    def test_contains_expected_fields(self):
        category = PrimaryCategoryFactory()
        serializer = PrimaryCategorySerializer(category)
        assert set(serializer.data.keys()) == {'name', 'slug', 'price_comparison_data'}

    def test_name_field_value(self):
        category = PrimaryCategoryFactory(name='Dairy')
        serializer = PrimaryCategorySerializer(category)
        assert serializer.data['name'] == 'Dairy'

    def test_slug_auto_generated_from_name(self):
        category = PrimaryCategoryFactory(name='Fresh Bread')
        serializer = PrimaryCategorySerializer(category)
        assert serializer.data['slug'] == 'fresh-bread'

    def test_price_comparison_data_defaults_to_empty_dict(self):
        category = PrimaryCategoryFactory()
        serializer = PrimaryCategorySerializer(category)
        assert serializer.data['price_comparison_data'] == {}
