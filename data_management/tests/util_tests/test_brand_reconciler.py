import os
import tempfile
import pytest
from products.models import Product, ProductBrand
from products.tests.factories import ProductBrandFactory, ProductFactory
from data_management.database_updating_classes.product_updating.post_processing.brand_reconciler import BrandReconciler


def _write_translation_table(path, mapping: dict):
    import json
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f)


@pytest.fixture
def reconciler(mock_command, tmp_path):
    """Returns a BrandReconciler pointed at a temp translation table file."""
    table_path = str(tmp_path / 'brand_translation_table.json')
    r = BrandReconciler(mock_command)
    r.translation_table_path = table_path
    return r, table_path


@pytest.mark.django_db
class TestBrandReconcilerLoadTranslationTable:
    def test_missing_file_returns_empty_dict(self, mock_command):
        r = BrandReconciler(mock_command)
        r.translation_table_path = '/nonexistent/path/brand_table.json'
        assert r._load_translation_table() == {}

    def test_empty_file_returns_empty_dict(self, mock_command, tmp_path):
        table_path = str(tmp_path / 'brand_translation_table.json')
        open(table_path, 'w').close()
        r = BrandReconciler(mock_command)
        r.translation_table_path = table_path
        assert r._load_translation_table() == {}

    def test_valid_file_returns_correct_mapping(self, mock_command, tmp_path):
        table_path = str(tmp_path / 'brand_translation_table.json')
        _write_translation_table(table_path, {'dupe-brand': 'canonical-brand'})
        r = BrandReconciler(mock_command)
        r.translation_table_path = table_path
        result = r._load_translation_table()
        assert result == {'dupe-brand': 'canonical-brand'}


@pytest.mark.django_db
class TestBrandReconcilerRun:
    def test_does_nothing_when_translation_table_empty(self, reconciler):
        r, table_path = reconciler
        open(table_path, 'w').close()  # empty file
        canonical = ProductBrandFactory(normalized_name='canonical-brand')

        r.run()

        assert ProductBrand.objects.filter(pk=canonical.pk).exists()

    def test_merges_duplicate_brand_into_canonical(self, reconciler):
        r, table_path = reconciler
        canonical = ProductBrandFactory(normalized_name='canonical-brand')
        dupe = ProductBrandFactory(normalized_name='dupe-brand')
        _write_translation_table(table_path, {'dupe-brand': 'canonical-brand'})

        r.run()

        assert not ProductBrand.objects.filter(pk=dupe.pk).exists()
        assert ProductBrand.objects.filter(pk=canonical.pk).exists()

    def test_reassigns_products_from_duplicate_to_canonical(self, reconciler):
        r, table_path = reconciler
        canonical = ProductBrandFactory(normalized_name='canonical-brand')
        dupe = ProductBrandFactory(normalized_name='dupe-brand')
        product = ProductFactory(brand=dupe)
        _write_translation_table(table_path, {'dupe-brand': 'canonical-brand'})

        r.run()

        product.refresh_from_db()
        assert product.brand_id == canonical.pk

    def test_merges_name_variations_into_canonical(self, reconciler):
        r, table_path = reconciler
        canonical = ProductBrandFactory(
            normalized_name='canonical-brand',
            normalized_name_variations=['canonical-brand'],
        )
        dupe = ProductBrandFactory(
            normalized_name='dupe-brand',
            normalized_name_variations=['dupe-brand'],
        )
        _write_translation_table(table_path, {'dupe-brand': 'canonical-brand'})

        r.run()

        canonical.refresh_from_db()
        assert 'dupe-brand' in canonical.normalized_name_variations

    def test_does_not_crash_when_canonical_brand_missing_from_db(self, reconciler):
        r, table_path = reconciler
        # Only dupe exists, canonical does not → no merge should happen
        ProductBrandFactory(normalized_name='dupe-brand')
        _write_translation_table(table_path, {'dupe-brand': 'missing-canonical'})

        r.run()  # Should not raise
        assert ProductBrand.objects.filter(normalized_name='dupe-brand').exists()

    def test_does_not_merge_brand_with_itself(self, reconciler):
        r, table_path = reconciler
        brand = ProductBrandFactory(normalized_name='my-brand')
        _write_translation_table(table_path, {'my-brand': 'my-brand'})

        r.run()

        assert ProductBrand.objects.filter(pk=brand.pk).exists()
