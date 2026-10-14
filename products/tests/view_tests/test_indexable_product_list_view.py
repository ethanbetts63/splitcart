import pytest
from django.urls import reverse
from django.utils.text import slugify

from companies.tests.factories import CompanyFactory
from products.tests.factories import PriceFactory, ProductFactory


@pytest.fixture(autouse=True)
def disable_cache(settings):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@pytest.mark.django_db
def test_lists_only_indexable_products_by_slug(client):
    compared = ProductFactory(name='Weet-Bix 1.2kg')
    for chain in ('Coles', 'Woolworths'):
        PriceFactory(product=compared, company=CompanyFactory(name=chain))
    PriceFactory(product=ProductFactory(name='Woolworths only'), company=CompanyFactory(name='Woolworths'))

    response = client.get(reverse('indexable-product-list'))

    assert response.status_code == 200
    assert response.json() == [{'slug': f'{slugify(compared.name)}-{compared.pk}'}]
