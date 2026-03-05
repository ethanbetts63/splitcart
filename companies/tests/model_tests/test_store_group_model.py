import pytest
from companies.models import StoreGroup
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestStoreGroupModel:
    def test_str_includes_company_name_and_id(self):
        company = CompanyFactory(name='Coles')
        group = StoreGroup.objects.create(company=company)
        assert str(group) == f'Coles Group {group.id}'

    def test_anchor_defaults_to_none(self):
        company = CompanyFactory()
        group = StoreGroup.objects.create(company=company)
        assert group.anchor is None

    def test_anchor_can_be_assigned(self):
        company = CompanyFactory()
        store = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company, anchor=store)
        assert group.anchor == store

    def test_anchor_set_null_on_store_delete(self):
        company = CompanyFactory()
        store = StoreFactory(company=company)
        group = StoreGroup.objects.create(company=company, anchor=store)
        store.delete()
        group.refresh_from_db()
        assert group.anchor is None
