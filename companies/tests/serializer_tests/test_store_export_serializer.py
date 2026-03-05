import pytest
from companies.models import Store
from companies.serializers.store_export_serializer import StoreExportSerializer
from companies.tests.factories import CompanyFactory, StoreFactory, DivisionFactory


@pytest.mark.django_db
class TestStoreExportSerializer:
    def test_contains_expected_fields(self):
        store = StoreFactory()
        serializer = StoreExportSerializer(store)
        assert set(serializer.data.keys()) == {'id', 'company', 'division', 'latitude', 'longitude'}

    def test_company_field_is_company_name(self):
        company = CompanyFactory(name='Woolworths')
        store = StoreFactory(company=company)
        serializer = StoreExportSerializer(store)
        assert serializer.data['company'] == 'Woolworths'

    def test_division_field_is_division_name(self):
        company = CompanyFactory()
        division = DivisionFactory(name='Woolworths Metro', company=company)
        store = StoreFactory(company=company, division=division)
        serializer = StoreExportSerializer(store)
        assert serializer.data['division'] == 'Woolworths Metro'

    def test_division_is_null_when_store_has_no_division(self):
        company = CompanyFactory()
        store = Store.objects.create(store_name='No Division Store', company=company, store_id='no-div-ser-1')
        serializer = StoreExportSerializer(store)
        assert serializer.data['division'] is None
