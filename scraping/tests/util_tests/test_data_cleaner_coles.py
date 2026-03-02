import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes


@pytest.fixture
def cleaner():
    return DataCleanerColes(
        raw_product_list=[],
        company='Coles',
        store_name='Coles Test',
        store_id='COL:001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


RAW_PRODUCT = {
    '_type': 'PRODUCT',
    'id': '12345',
    'name': 'Full Cream Milk',
    'brand': 'Coles',
    'barcode': None,
    'description': 'Fresh milk',
    'size': '2L',
    'pricing': {
        'now': 2.50,
        'was': 3.50,
        'comparable': '$1.25 per 1L',
        'unit': {'price': 1.25, 'ofMeasureUnits': '1L'},
    },
    'onlineHeirs': [
        {'subCategory': 'Dairy', 'category': 'Milk & Cream', 'aisle': 'Chilled'}
    ],
    'availability': True,
}

RAW_PRODUCT_NOT_ON_SPECIAL = {
    **RAW_PRODUCT,
    'pricing': {
        'now': 2.50,
        'was': 0,
        'comparable': '$1.25 per 1L',
        'unit': {'price': 1.25, 'ofMeasureUnits': '1L'},
    },
}


class TestIsValidProduct:
    def test_product_type_is_valid(self, cleaner):
        assert cleaner._is_valid_product({'_type': 'PRODUCT'}) is True

    def test_banner_type_is_invalid(self, cleaner):
        assert cleaner._is_valid_product({'_type': 'BANNER'}) is False

    def test_none_is_invalid(self, cleaner):
        assert cleaner._is_valid_product(None) is False

    def test_missing_type_is_invalid(self, cleaner):
        assert cleaner._is_valid_product({'name': 'Milk'}) is False


class TestTransformProductPrice:
    def test_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['is_on_special'] is True
        assert result['price_current'] == 2.50
        assert result['price_was'] == 3.50
        assert result['price_save_amount'] == 1.00

    def test_was_price_zero_becomes_not_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_NOT_ON_SPECIAL)
        assert result['price_was'] is None
        assert result['is_on_special'] is False


class TestTransformProductUrl:
    def test_url_constructed_from_sku_and_slugified_name(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['url'] == 'https://www.coles.com.au/product/full-cream-milk-12345'


class TestTransformProductCategoryPath:
    def test_category_path_extracted_from_online_heirs(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert 'Dairy' in result['category_path']
        assert 'Milk & Cream' in result['category_path']
        assert 'Chilled' in result['category_path']

    def test_empty_online_heirs_gives_empty_path(self, cleaner):
        raw = {**RAW_PRODUCT, 'onlineHeirs': []}
        result = cleaner._transform_product(raw)
        assert result['category_path'] == []


class TestTransformProductUnitPrice:
    def test_unit_price_standardized_to_per_1l(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result.get('unit_of_measure') == '1l'
        assert result.get('unit_price') == pytest.approx(1.25)
