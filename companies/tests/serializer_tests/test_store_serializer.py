import pytest
from companies.serializers.store_serializer import StoreSerializer
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestStoreSerializer:
    def test_contains_expected_fields(self):
        store = StoreFactory()
        serializer = StoreSerializer(store)
        assert set(serializer.data.keys()) == {'id', 'store_name', 'latitude', 'longitude', 'company_name'}

    def test_company_name_sourced_from_related_company(self):
        company = CompanyFactory(name='Aldi')
        store = StoreFactory(company=company)
        serializer = StoreSerializer(store)
        assert serializer.data['company_name'] == 'Aldi'

    def test_store_name_field_value(self):
        store = StoreFactory(store_name='Coles Perth CBD')
        serializer = StoreSerializer(store)
        assert serializer.data['store_name'] == 'Coles Perth CBD'
