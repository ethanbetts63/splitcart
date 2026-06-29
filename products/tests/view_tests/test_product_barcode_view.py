import json

import pytest
from django.urls import reverse

from companies.tests.factories import CompanyFactory
from products.models import SKU
from products.tests.factories import ProductFactory


@pytest.mark.django_db
class TestProductBarcodeView:
    def test_requires_internal_api_key(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        response = client.post(
            reverse('product-barcodes'),
            data=json.dumps({'skus': [123]}),
            content_type='application/json',
        )

        assert response.status_code == 401

    def test_returns_barcodes_for_matching_coles_skus(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        coles = CompanyFactory(name='Coles')
        woolworths = CompanyFactory(name='Woolworths')
        product = ProductFactory(barcode='9300000000001')
        other_product = ProductFactory(barcode='9300000000002')
        SKU.objects.create(company=coles, product=product, sku='123')
        SKU.objects.create(company=woolworths, product=other_product, sku='456')

        response = client.post(
            reverse('product-barcodes'),
            data=json.dumps({'skus': [123, 456, 'bad-value']}),
            content_type='application/json',
            HTTP_X_INTERNAL_API_KEY='test-key',
        )

        assert response.status_code == 200
        assert response.json() == {
            '123': {
                'barcode': '9300000000001',
                'has_no_coles_barcode': False,
            }
        }

    def test_returns_has_no_coles_barcode_flag(self, client, monkeypatch):
        monkeypatch.setenv('INTERNAL_API_KEY', 'test-key')
        coles = CompanyFactory(name='Coles')
        product = ProductFactory(barcode=None, has_no_coles_barcode=True)
        SKU.objects.create(company=coles, product=product, sku='789')

        response = client.post(
            reverse('product-barcodes'),
            data=json.dumps({'skus': [789]}),
            content_type='application/json',
            HTTP_X_INTERNAL_API_KEY='test-key',
        )

        assert response.status_code == 200
        assert response.json() == {
            '789': {
                'barcode': None,
                'has_no_coles_barcode': True,
            }
        }
