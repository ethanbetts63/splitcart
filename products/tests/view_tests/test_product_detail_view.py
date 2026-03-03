import pytest
from django.urls import reverse
from products.tests.factories import ProductFactory


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.mark.django_db
class TestProductDetailView:
    def test_returns_200_for_existing_product(self, client):
        product = ProductFactory()
        response = client.get(reverse('product-detail', kwargs={'pk': product.pk}))
        assert response.status_code == 200

    def test_returns_correct_product_data(self, client):
        product = ProductFactory(name='Weet-Bix')
        response = client.get(reverse('product-detail', kwargs={'pk': product.pk}))
        data = response.json()
        assert data['name'] == 'Weet-Bix'
        assert data['id'] == product.pk

    def test_returns_404_for_nonexistent_product(self, client):
        response = client.get(reverse('product-detail', kwargs={'pk': 99999}))
        assert response.status_code == 404
