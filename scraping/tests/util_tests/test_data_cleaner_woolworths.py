import pytest
import json
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerWoolworths import DataCleanerWoolworths


@pytest.fixture
def cleaner():
    return DataCleanerWoolworths(
        raw_product_list=[],
        company='Woolworths',
        store_name='Woolworths Test',
        store_id='WOW001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


RAW_PRODUCT = {
    'Stockcode': 67890,
    'Name': 'Full Cream Milk',
    'Brand': 'Dairy Farmers',
    'Barcode': '9310088000010',
    'PackageSize': '2L',
    'UrlFriendlyName': 'dairy-farmers-full-cream-milk',
    'Price': 3.20,
    'WasPrice': 4.00,
    'CupString': '$1.60 per 1L',
    'InstoreCupPrice': None,
    'CupMeasure': '1L',
    'Rating': {'Average': 4.5, 'ReviewCount': 120},
    'AdditionalAttributes': {
        'piesdepartmentnamesjson': json.dumps(['Dairy, Eggs & Fridge']),
        'piescategorynamesjson': json.dumps(['Milk']),
        'piessubcategorynamesjson': json.dumps(['Full Cream Milk']),
        'healthstarrating': '4.0',
        'ingredients': 'Milk',
        'allergystatement': 'Contains milk',
        'countryoforigin': 'Australia',
    },
    'IsAvailable': True,
}

RAW_PRODUCT_NOT_ON_SPECIAL = {
    **RAW_PRODUCT,
    'WasPrice': None,
}


class TestTransformProductPrice:
    def test_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['is_on_special'] is True
        assert result['price_current'] == 3.20
        assert result['price_was'] == 4.00

    def test_not_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_NOT_ON_SPECIAL)
        assert result['is_on_special'] is False
        assert result['price_was'] is None


class TestTransformProductUrl:
    def test_url_includes_stockcode_and_slug(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['url'] == (
            'https://www.woolworths.com.au/shop/productdetails/67890/dairy-farmers-full-cream-milk'
        )

    def test_full_url_not_built_when_stockcode_missing(self, cleaner):
        raw = {**RAW_PRODUCT, 'Stockcode': None}
        result = cleaner._transform_product(raw)
        # Without stockcode the URL isn't reconstructed into the full path
        url = result.get('url', '')
        assert 'woolworths.com.au/shop/productdetails' not in str(url)


class TestTransformProductHealthStarRating:
    def test_hsr_parsed_to_float(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['health_star_rating'] == 4.0
        assert isinstance(result['health_star_rating'], float)

    def test_invalid_hsr_becomes_none(self, cleaner):
        raw = {
            **RAW_PRODUCT,
            'AdditionalAttributes': {
                **RAW_PRODUCT['AdditionalAttributes'],
                'healthstarrating': 'not-a-number',
            }
        }
        result = cleaner._transform_product(raw)
        assert result.get('health_star_rating') is None


class TestTransformProductCategoryPath:
    def test_category_path_built_from_json_fields(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert len(result['category_path']) >= 1
        assert 'Dairy, Eggs & Fridge' in result['category_path']
        assert 'Milk' in result['category_path']

    def test_duplicate_categories_deduplicated(self, cleaner):
        raw = {
            **RAW_PRODUCT,
            'AdditionalAttributes': {
                **RAW_PRODUCT['AdditionalAttributes'],
                'piesdepartmentnamesjson': json.dumps(['Dairy']),
                'piescategorynamesjson': json.dumps(['Dairy']),  # duplicate
                'piessubcategorynamesjson': json.dumps(['Milk']),
            }
        }
        result = cleaner._transform_product(raw)
        assert result['category_path'].count('Dairy') == 1


class TestTransformProductAvailability:
    def test_is_available_true(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['is_available'] is True

    def test_is_available_false(self, cleaner):
        raw = {**RAW_PRODUCT, 'IsAvailable': False}
        result = cleaner._transform_product(raw)
        assert result['is_available'] is False
