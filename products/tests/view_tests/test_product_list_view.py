import pytest
from django.urls import reverse
from products.tests.factories import ProductFactory, PriceFactory


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.mark.django_db
class TestProductListView:
    def test_returns_200_without_store_ids(self, client):
        response = client.get(reverse('product-list'))
        assert response.status_code == 200

    def test_returns_empty_when_no_store_ids_provided(self, client):
        ProductFactory()
        response = client.get(reverse('product-list'))
        data = response.json()
        assert data['count'] == 0

    def test_returns_products_at_requested_store(self, client, make_anchored_store):
        store = make_anchored_store()
        product = ProductFactory()
        PriceFactory(product=product, store=store)

        response = client.get(reverse('product-list'), {'store_ids': str(store.id)})
        data = response.json()

        assert data['count'] == 1

    def test_search_filters_results_by_name(self, client, make_anchored_store):
        store = make_anchored_store()
        weetbix = ProductFactory(name='Weet-Bix', normalized_name_brand_size='weetbix-view-test')
        cornflakes = ProductFactory(name='Corn Flakes', normalized_name_brand_size='cornflakes-view-test')
        PriceFactory(product=weetbix, store=store)
        PriceFactory(product=cornflakes, store=store)

        response = client.get(reverse('product-list'), {'store_ids': str(store.id), 'search': 'Weet-Bix'})
        data = response.json()

        names = [r['name'] for r in data['results']]
        assert 'Weet-Bix' in names
        assert 'Corn Flakes' not in names

    def test_default_page_size_is_20(self, client, make_anchored_store):
        store = make_anchored_store()
        products = ProductFactory.create_batch(25)
        for product in products:
            PriceFactory(product=product, store=store)

        response = client.get(reverse('product-list'), {'store_ids': str(store.id)})
        data = response.json()

        assert data['count'] == 25
        assert len(data['results']) == 20
