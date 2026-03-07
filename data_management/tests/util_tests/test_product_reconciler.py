import datetime
import pytest
from decimal import Decimal
from products.models import Product, Price
from products.tests.factories import ProductFactory, PriceFactory
from companies.tests.factories import StoreFactory
from data_management.database_updating_classes.product_updating.post_processing.product_reconciler import ProductReconciler


def _write_translation_table(path, mapping: dict):
    import json
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f)


@pytest.fixture
def reconciler(mock_command, tmp_path):
    """Returns a ProductReconciler pointed at a temp translation table file."""
    table_path = str(tmp_path / 'product_translation_table.json')
    r = ProductReconciler(mock_command)
    r.translation_table_path = table_path
    return r, table_path


@pytest.mark.django_db
class TestProductReconcilerLoadTranslationTable:
    def test_missing_file_returns_empty_dict(self, mock_command):
        r = ProductReconciler(mock_command)
        r.translation_table_path = '/nonexistent/path/product_table.json'
        assert r._load_translation_table() == {}

    def test_empty_file_returns_empty_dict(self, mock_command, tmp_path):
        table_path = str(tmp_path / 'product_translation_table.json')
        open(table_path, 'w').close()
        r = ProductReconciler(mock_command)
        r.translation_table_path = table_path
        assert r._load_translation_table() == {}

    def test_valid_file_returns_correct_mapping(self, mock_command, tmp_path):
        table_path = str(tmp_path / 'product_translation_table.json')
        _write_translation_table(table_path, {'dupe-product': 'canonical-product'})
        r = ProductReconciler(mock_command)
        r.translation_table_path = table_path
        result = r._load_translation_table()
        assert result == {'dupe-product': 'canonical-product'}


@pytest.mark.django_db
class TestProductReconcilerRun:
    def test_does_nothing_when_translation_table_empty(self, reconciler):
        r, table_path = reconciler
        open(table_path, 'w').close()
        canonical = ProductFactory(normalized_name_brand_size='canonical-product')

        r.run()

        assert Product.objects.filter(pk=canonical.pk).exists()

    def test_deletes_duplicate_product(self, reconciler):
        r, table_path = reconciler
        canonical = ProductFactory(normalized_name_brand_size='canonical-product')
        dupe = ProductFactory(normalized_name_brand_size='dupe-product')
        _write_translation_table(table_path, {'dupe-product': 'canonical-product'})

        r.run()

        assert not Product.objects.filter(pk=dupe.pk).exists()
        assert Product.objects.filter(pk=canonical.pk).exists()

    def test_reassigns_dupe_price_to_canonical(self, reconciler):
        r, table_path = reconciler
        store = StoreFactory()
        canonical = ProductFactory(normalized_name_brand_size='canonical-product')
        dupe = ProductFactory(normalized_name_brand_size='dupe-product')
        dupe_price = PriceFactory(product=dupe, store=store, price=Decimal('3.00'))
        _write_translation_table(table_path, {'dupe-product': 'canonical-product'})

        r.run()

        # The price should now point at the canonical product
        assert Price.objects.filter(pk=dupe_price.pk, product=canonical).exists()

    def test_keeps_most_recent_price_when_both_have_same_store(self, reconciler):
        r, table_path = reconciler
        store = StoreFactory()
        canonical = ProductFactory(normalized_name_brand_size='canonical-product')
        dupe = ProductFactory(normalized_name_brand_size='dupe-product')

        old_date = datetime.date.today() - datetime.timedelta(days=10)
        new_date = datetime.date.today()

        canonical_price = PriceFactory(product=canonical, store=store, price=Decimal('5.00'), scraped_date=new_date)
        dupe_price = PriceFactory(product=dupe, store=store, price=Decimal('3.00'), scraped_date=old_date)
        _write_translation_table(table_path, {'dupe-product': 'canonical-product'})

        r.run()

        # Canonical price (newer) survives; dupe price (older) is deleted
        assert Price.objects.filter(pk=canonical_price.pk).exists()
        assert not Price.objects.filter(pk=dupe_price.pk).exists()

    def test_does_not_crash_when_canonical_missing_from_db(self, reconciler):
        r, table_path = reconciler
        ProductFactory(normalized_name_brand_size='dupe-product')
        _write_translation_table(table_path, {'dupe-product': 'missing-canonical'})

        r.run()  # Should not raise
        assert Product.objects.filter(normalized_name_brand_size='dupe-product').exists()

    def test_does_not_merge_product_with_itself(self, reconciler):
        r, table_path = reconciler
        product = ProductFactory(normalized_name_brand_size='my-product')
        _write_translation_table(table_path, {'my-product': 'my-product'})

        r.run()

        assert Product.objects.filter(pk=product.pk).exists()

    def test_enriches_canonical_with_dupe_data(self, reconciler):
        r, table_path = reconciler
        canonical = ProductFactory(normalized_name_brand_size='canonical-product', barcode=None)
        dupe = ProductFactory(normalized_name_brand_size='dupe-product', barcode='9310072001646')
        _write_translation_table(table_path, {'dupe-product': 'canonical-product'})

        r.run()

        canonical.refresh_from_db()
        assert canonical.barcode == '9310072001646'
