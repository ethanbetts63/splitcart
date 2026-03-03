import pytest
from django.urls import reverse
from products.tests.factories import ProductFactory, ProductSubstitutionFactory


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.mark.django_db
class TestProductSubstituteListView:
    def _url(self, product_id):
        return reverse('product-substitute-list', kwargs={'product_id': product_id})

    def test_returns_200(self, client):
        product = ProductFactory()
        response = client.get(self._url(product.pk))
        assert response.status_code == 200

    def test_returns_substitutes_where_product_is_product_a(self, client):
        product = ProductFactory()
        substitute = ProductFactory()
        ProductSubstitutionFactory(product_a=product, product_b=substitute, score=0.9)

        response = client.get(self._url(product.pk))
        data = response.json()

        assert len(data) == 1

    def test_returns_substitutes_where_product_is_product_b(self, client):
        product = ProductFactory()
        substitute = ProductFactory()
        ProductSubstitutionFactory(product_a=substitute, product_b=product, score=0.9)

        response = client.get(self._url(product.pk))
        data = response.json()

        assert len(data) == 1

    def test_returns_at_most_5_substitutes(self, client):
        product = ProductFactory()
        for _ in range(7):
            sub = ProductFactory()
            ProductSubstitutionFactory(product_a=product, product_b=sub, score=0.9)

        response = client.get(self._url(product.pk))
        data = response.json()

        assert len(data) <= 5

    def test_returns_empty_list_for_product_with_no_substitutes(self, client):
        product = ProductFactory()
        response = client.get(self._url(product.pk))
        data = response.json()
        assert data == []
