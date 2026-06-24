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
        'piesdepartmentnamesjson': json.dumps(['Dinner', 'Dairy, Eggs & Fridge']),
        'piescategorynamesjson': json.dumps(['Breakfast', 'Milk']),
        'piessubcategorynamesjson': json.dumps(['Health Shots & Drinks', 'Full Cream Milk']),
        'healthstarrating': '4.0',
        'ingredients': 'Milk',
        'allergystatement': 'Contains milk',
        'countryoforigin': 'Australia',
    },
    'category_path': ['Dairy, Eggs & Fridge', 'Milk', 'Full Cream Milk'],
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
    def test_category_path_uses_scrape_context_path(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['category_path'] == ['Dairy, Eggs & Fridge', 'Milk', 'Full Cream Milk']

    def test_pies_fields_do_not_pollute_category_path(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert 'Dinner' not in result['category_path']
        assert 'Breakfast' not in result['category_path']
        assert 'Health Shots & Drinks' not in result['category_path']

    def test_context_path_categories_deduplicated(self, cleaner):
        raw = {
            **RAW_PRODUCT,
            'category_path': ['Dairy', 'Dairy', 'Milk'],
        }
        result = cleaner._transform_product(raw)
        assert result['category_path'].count('Dairy') == 1

    def test_missing_context_path_gives_empty_path(self, cleaner):
        raw = {k: v for k, v in RAW_PRODUCT.items() if k != 'category_path'}
        result = cleaner._transform_product(raw)
        assert result['category_path'] == []


class TestTransformProductAvailability:
    def test_is_available_true(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT)
        assert result['is_available'] is True

    def test_is_available_false(self, cleaner):
        raw = {**RAW_PRODUCT, 'IsAvailable': False}
        result = cleaner._transform_product(raw)
        assert result['is_available'] is False
