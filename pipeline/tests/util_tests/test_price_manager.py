import datetime
import pytest
from decimal import Decimal
from products.models import Price
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import CompanyFactory
from pipeline.database_updating_classes.product_updating.price_manager import PriceManager


def _make_caches(product_id, company_id, existing_price=None):
    """Build the minimal caches that PriceManager expects."""
    products_by_norm_string = {'test-product': product_id}

    if existing_price:
        hash_to_pk = {existing_price.price_hash: existing_price.pk} if existing_price.price_hash else {}
        product_id_to_pk = {product_id: existing_price.pk}
    else:
        hash_to_pk = {}
        product_id_to_pk = {}

    prices_by_company = {
        company_id: {
            'hash_to_pk': hash_to_pk,
            'product_id_to_pk': product_id_to_pk,
        }
    }
    return {'products_by_norm_string': products_by_norm_string, 'prices_by_company': prices_by_company}


def _raw_data(norm_string='test-product', price=2.50, price_hash='hash-abc', scraped_date='2025-01-01T00:00:00'):
    return [{
        'metadata': {'scraped_date': scraped_date},
        'product': {
            'normalized_name_brand_size': norm_string,
            'price_current': price,
            'price_hash': price_hash,
            'unit_price': None,
            'unit_of_measure': None,
            'per_unit_price_string': None,
            'is_on_special': False,
        }
    }]


@pytest.mark.django_db
class TestPriceManagerProcess:
    def test_creates_new_price_when_none_exists(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        caches = _make_caches(product.id, company.id)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(), company)

        assert Price.objects.filter(product=product, company=company).exists()

    def test_does_not_create_price_when_hash_unchanged(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        existing = PriceFactory(
            product=product, company=company,
            price=Decimal('2.50'), price_hash='hash-abc',
            scraped_date=datetime.date(2024, 12, 1),
        )
        caches = _make_caches(product.id, company.id, existing_price=existing)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(price_hash='hash-abc'), company)

        # Only one price should exist
        assert Price.objects.filter(product=product, company=company).count() == 1

    def test_updates_existing_price_when_hash_changed(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        existing = PriceFactory(
            product=product, company=company,
            price=Decimal('3.00'), price_hash='old-hash',
            scraped_date=datetime.date(2024, 12, 1),
        )
        caches = _make_caches(product.id, company.id, existing_price=existing)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(price=2.50, price_hash='new-hash'), company)

        existing.refresh_from_db()
        assert existing.price == Decimal('2.50')
        assert existing.price_hash == 'new-hash'

    def test_sets_was_price_on_update(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        existing = PriceFactory(
            product=product, company=company,
            price=Decimal('5.00'), price_hash='old-hash',
            scraped_date=datetime.date(2024, 12, 1),
        )
        caches = _make_caches(product.id, company.id, existing_price=existing)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(price=3.00, price_hash='new-hash'), company)

        existing.refresh_from_db()
        assert existing.was_price == Decimal('5.00')
        assert existing.save_amount == Decimal('2.00')

    def test_deletes_price_for_delisted_product(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        existing = PriceFactory(
            product=product, company=company,
            price=Decimal('2.00'), price_hash='old-hash',
            scraped_date=datetime.date(2024, 12, 1),
        )
        caches = _make_caches(product.id, company.id, existing_price=existing)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        # Send data for a different product — 'old-hash' is not in seen_hashes
        other_product = ProductFactory()
        caches['products_by_norm_string']['other-product'] = other_product.id
        manager.process(_raw_data(norm_string='other-product', price_hash='other-hash'), company)

        assert not Price.objects.filter(pk=existing.pk).exists()

    def test_skips_price_when_scraped_date_invalid(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        caches = _make_caches(product.id, company.id)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(scraped_date='not-a-date'), company)

        assert not Price.objects.filter(company=company).exists()

    def test_skips_product_not_in_cache(self, mock_command):
        company = CompanyFactory()
        caches = {'products_by_norm_string': {}, 'prices_by_company': {company.id: {'hash_to_pk': {}, 'product_id_to_pk': {}}}}
        manager = PriceManager(mock_command, caches, lambda *a: None)

        manager.process(_raw_data(norm_string='unknown-product'), company)

        assert not Price.objects.filter(company=company).exists()

    def test_skips_null_price_current(self, mock_command):
        product = ProductFactory()
        company = CompanyFactory()
        caches = _make_caches(product.id, company.id)
        manager = PriceManager(mock_command, caches, lambda *a: None)

        data = _raw_data()
        data[0]['product']['price_current'] = None
        manager.process(data, company)

        assert not Price.objects.filter(product=product, company=company).exists()
