import pytest
from django.db import IntegrityError
from companies.models import Store
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestStoreModel:
    def test_str_returns_name_and_company(self):
        company = CompanyFactory(name='IGA')
        store = StoreFactory(store_name='IGA Cannington', company=company)
        assert str(store) == 'IGA Cannington (IGA)'

    def test_unique_together_company_store_id(self):
        company = CompanyFactory()
        Store.objects.create(store_name='Store A', company=company, store_id='abc-123')
        with pytest.raises(IntegrityError):
            Store.objects.create(store_name='Store B', company=company, store_id='abc-123')

    def test_same_store_id_allowed_for_different_companies(self):
        company_a = CompanyFactory()
        company_b = CompanyFactory()
        StoreFactory(company=company_a, store_id='shared-id')
        StoreFactory(company=company_b, store_id='shared-id')  # should not raise

    def test_division_nullable(self):
        company = CompanyFactory()
        store = Store.objects.create(store_name='No Division Store', company=company, store_id='no-div-1')
        assert store.division is None

    def test_needs_rescraping_defaults_to_false(self):
        store = StoreFactory()
        assert store.needs_rescraping is False

    def test_last_scraped_nullable(self):
        store = StoreFactory()
        assert store.last_scraped is None

    def test_scheduled_at_nullable(self):
        store = StoreFactory()
        assert store.scheduled_at is None
