import pytest
from django.urls import reverse
from companies.models import StoreGroup, StoreGroupMembership
from companies.tests.factories import CompanyFactory, StoreFactory


@pytest.mark.django_db
class TestExportAnchorStoresView:
    def test_returns_403_without_api_key(self, client):
        response = client.get(reverse('export-anchor-stores'))
        assert response.status_code == 403

    def test_returns_200_with_valid_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.status_code == 200

    def test_returns_empty_list_when_no_groups(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []

    def test_returns_anchor_store_id_when_anchor_has_prices(self, client, monkeypatch):
        from products.tests.factories import PriceFactory, ProductFactory
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        PriceFactory(store=anchor_store, product=ProductFactory())

        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert anchor_store.id in data

    def test_excludes_anchor_store_without_prices(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        company = CompanyFactory()
        anchor_store = StoreFactory(company=company)
        StoreGroup.objects.create(company=company, anchor=anchor_store)
        # No prices for this anchor store

        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        data = response.json()
        assert anchor_store.id not in data

    def test_excludes_groups_with_no_anchor(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        company = CompanyFactory()
        StoreGroup.objects.create(company=company, anchor=None)

        response = client.get(reverse('export-anchor-stores'), HTTP_X_INTERNAL_API_KEY='test-key')
        assert response.json() == []
