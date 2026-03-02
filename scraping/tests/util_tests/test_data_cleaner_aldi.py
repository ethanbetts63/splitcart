import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerAldi import DataCleanerAldi


@pytest.fixture
def cleaner():
    return DataCleanerAldi(
        raw_product_list=[],
        company='ALDI',
        store_name='ALDI Test',
        store_id='ALDI001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


RAW_PRODUCT = {
    'sku': 'A12345',
    'name': 'Full Cream Milk',
    'brandName': 'ALDI',
    'sellingSize': '2L',
    'urlSlugText': 'full-cream-milk',
    'assets': [{'url': 'https://cdn.aldi.com.au/product.jpg'}],
    'categories': [{'name': 'Dairy'}, {'name': 'Milk'}],
    'price': {
        'amount': 290,
        'wasPriceDisplay': None,
        'comparisonDisplay': '$1.45 per 1L',
        'comparison': 145,
    },
    'notForSale': False,
}

RAW_PRODUCT_ON_SPECIAL = {
    **RAW_PRODUCT,
    'price': {
        'amount': 290,
        'wasPriceDisplay': '$3.50',
        'comparisonDisplay': '$1.45 per 1L',
        'comparison': 145,
    },
}

RAW_PRODUCT_TEMPLATED_IMAGE = {
    **RAW_PRODUCT,
    'assets': [{'url': 'https://cdn.aldi.com.au/product-{width}.jpg/{slug}'}],
}


class TestTransformProductPrice:
    def test_price_converted_from_cents(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['price_current'] == pytest.approx(2.90)

    def test_was_price_none_when_not_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['price_was'] is None
        assert result['is_on_special'] is False

    def test_was_price_parsed_from_string(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result['price_was'] == pytest.approx(3.50)
        assert result['is_on_special'] is True

    def test_per_unit_price_converted_from_cents(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result.get('per_unit_price_value') == pytest.approx(1.45)


class TestTransformProductUrl:
    def test_url_constructed_from_slug_and_sku(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['url'] == 'https://www.aldi.com.au/product/full-cream-milk-A12345'


class TestTransformProductImageUrl:
    def test_width_placeholder_replaced(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_TEMPLATED_IMAGE)
        assert '{width}' not in result.get('aldi_image_url', '')
        assert '500' in result.get('aldi_image_url', '')

    def test_slug_suffix_removed(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_TEMPLATED_IMAGE)
        assert not result.get('aldi_image_url', '').endswith('/{slug}')

    def test_plain_image_url_passed_through(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result.get('aldi_image_url') == 'https://cdn.aldi.com.au/product.jpg'

    def test_no_assets_gives_none_image(self, cleaner):
        raw = {**RAW_PRODUCT, 'assets': []}
        result = cleaner._transform_product(raw)
        assert result.get('aldi_image_url') is None


class TestTransformProductCategoryPath:
    def test_categories_extracted_from_list_of_dicts(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert 'Dairy' in result['category_path']
        assert 'Milk' in result['category_path']

    def test_empty_categories_gives_empty_path(self, cleaner):
        raw = {**RAW_PRODUCT, 'categories': []}
        result = cleaner._transform_product(raw)
        assert result['category_path'] == []


class TestTransformProductAvailability:
    def test_not_for_sale_false_means_available(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['is_available'] is True

    def test_not_for_sale_true_means_unavailable(self, cleaner):
        raw = {**RAW_PRODUCT, 'notForSale': True}
        result = cleaner._transform_product(raw)
        assert result['is_available'] is False
