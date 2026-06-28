import pytest
from django.urls import reverse
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import CompanyFactory
from data_management.models import SystemSetting
from products.utils.default_companies import CACHE_KEY


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


def set_default_companies(company_ids):
    SystemSetting.objects.update_or_create(key=CACHE_KEY, defaults={'value': company_ids})


@pytest.mark.django_db
class TestProductListView:
    def test_returns_200_without_default_companies(self, client):
        response = client.get(reverse('product-list'))
        assert response.status_code == 200

    def test_returns_empty_when_no_default_companies_configured(self, client):
        ProductFactory()
        response = client.get(reverse('product-list'))
        data = response.json()
        assert data['count'] == 0

    def test_returns_products_at_default_companies(self, client):
        company = CompanyFactory()
        product = ProductFactory()
        PriceFactory(product=product, company=company)
        set_default_companies([company.id])

        response = client.get(reverse('product-list'))
        data = response.json()

        assert data['count'] == 1

    def test_search_filters_results_by_name(self, client):
        company = CompanyFactory()
        weetbix = ProductFactory(name='Weet-Bix', normalized_name_brand_size='weetbix-view-test')
        cornflakes = ProductFactory(name='Corn Flakes', normalized_name_brand_size='cornflakes-view-test')
        PriceFactory(product=weetbix, company=company)
        PriceFactory(product=cornflakes, company=company)
        set_default_companies([company.id])

        response = client.get(reverse('product-list'), {'search': 'Weet-Bix'})
        data = response.json()

        names = [r['name'] for r in data['results']]
        assert 'Weet-Bix' in names
        assert 'Corn Flakes' not in names

    def test_default_page_size_is_20(self, client):
        company = CompanyFactory()
        products = ProductFactory.create_batch(25)
        for product in products:
            PriceFactory(product=product, company=company)
        set_default_companies([company.id])

        response = client.get(reverse('product-list'))
        data = response.json()

        assert data['count'] == 25
        assert len(data['results']) == 20
