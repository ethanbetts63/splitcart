import json
import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerWoolworths import DataCleanerWoolworths
from scraping.utils.product_scraping_utils.DataCleanerColes import DataCleanerColes
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga
from scraping.utils.product_scraping_utils.DataCleanerAldi import DataCleanerAldi

_TIMESTAMP = datetime(2024, 6, 15)


def _make_cleaner(cls, products):
    return cls(
        raw_product_list=products,
        company='Test',
        store_name='Test Store',
        store_id='TEST001',
        state='nsw',
        timestamp=_TIMESTAMP,
        brand_translations={},
        product_translations={},
    )


def _first_product(cleaner):
    return cleaner.clean_data()['products'][0]


# ---------------------------------------------------------------------------
# Woolworths
# ---------------------------------------------------------------------------

_WOW_BASE = {
    'Stockcode': 67890,
    'Name': 'Full Cream Milk',
    'Brand': 'Dairy Farmers',
    'Barcode': '9310088000010',
    'PackageSize': '2L',
    'UrlFriendlyName': 'dairy-farmers-full-cream-milk',
    'Price': 3.20,
    'WasPrice': None,
    'CupString': '$1.60 per 1L',
    'InstoreCupPrice': None,
    'CupMeasure': '1L',
    'Rating': {'Average': 4.5, 'ReviewCount': 120},
    'AdditionalAttributes': {
        'piesdepartmentnamesjson': json.dumps(['Dairy, Eggs & Fridge']),
        'piescategorynamesjson': json.dumps(['Milk']),
        'piessubcategorynamesjson': json.dumps(['Full Cream Milk']),
        'healthstarrating': '4.0',
    },
    'IsAvailable': True,
}


class TestWoolworthsNormalization:
    def test_size_l_converted_to_ml(self):
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert product['sizes'] == ['2000ml']

    def test_kg_size_converted_to_grams(self):
        raw = {**_WOW_BASE, 'PackageSize': '0.5kg'}
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [raw]))
        assert '500g' in product['sizes']

    def test_multipack_size_extracted(self):
        raw = {**_WOW_BASE, 'Name': 'Coke Can 6 x 375mL', 'PackageSize': '6 x 375mL'}
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [raw]))
        assert '375ml' in product['sizes']
        assert '6pk' in product['sizes']

    def test_normalized_brand_is_cleaned_lowercase(self):
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert product['normalized_brand'] == 'dairy farmers'

    def test_no_brand_means_no_normalized_brand_field(self):
        raw = {**_WOW_BASE, 'Brand': None}
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [raw]))
        assert 'normalized_brand' not in product

    def test_normalized_name_brand_size_is_sorted_bag_of_words(self):
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert product['normalized_name_brand_size'] == '2000ml cream dairy farmers full milk'

    def test_valid_ean13_barcode_preserved(self):
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert product['barcode'] == '9310088000010'

    def test_twelve_digit_barcode_padded_to_thirteen(self):
        raw = {**_WOW_BASE, 'Barcode': '123456789012'}
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [raw]))
        assert product['barcode'] == '0123456789012'

    def test_invalid_barcode_string_absent_from_output(self):
        raw = {**_WOW_BASE, 'Barcode': 'notfound'}
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [raw]))
        assert product.get('barcode') is None

    def test_price_hash_is_present_and_is_string(self):
        product = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert isinstance(product.get('price_hash'), str)

    def test_price_hash_is_deterministic(self):
        p1 = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        p2 = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        assert p1['price_hash'] == p2['price_hash']

    def test_price_hash_changes_when_price_changes(self):
        cheaper = {**_WOW_BASE, 'Price': 2.00}
        p1 = _first_product(_make_cleaner(DataCleanerWoolworths, [_WOW_BASE]))
        p2 = _first_product(_make_cleaner(DataCleanerWoolworths, [cheaper]))
        assert p1['price_hash'] != p2['price_hash']


# ---------------------------------------------------------------------------
# Coles
# ---------------------------------------------------------------------------

_COLES_BASE = {
    '_type': 'PRODUCT',
    'id': '12345',
    'name': 'Full Cream Milk',
    'brand': 'Dairy Farmers',
    'barcode': None,
    'size': '2L',
    'pricing': {
        'now': 3.20,
        'was': 0,
        'comparable': '$1.60 per 1L',
        'unit': {'price': 1.60, 'ofMeasureUnits': '1L'},
    },
    'onlineHeirs': [
        {'subCategory': 'Dairy', 'category': 'Milk', 'aisle': 'Chilled'}
    ],
}


class TestColesNormalization:
    def test_size_l_converted_to_ml(self):
        product = _first_product(_make_cleaner(DataCleanerColes, [_COLES_BASE]))
        assert product['sizes'] == ['2000ml']

    def test_kg_size_converted_to_grams(self):
        raw = {**_COLES_BASE, 'size': '500g'}
        product = _first_product(_make_cleaner(DataCleanerColes, [raw]))
        assert '500g' in product['sizes']

    def test_normalized_brand_is_cleaned_lowercase(self):
        product = _first_product(_make_cleaner(DataCleanerColes, [_COLES_BASE]))
        assert product['normalized_brand'] == 'dairy farmers'

    def test_normalized_name_brand_size_is_sorted_bag_of_words(self):
        product = _first_product(_make_cleaner(DataCleanerColes, [_COLES_BASE]))
        assert product['normalized_name_brand_size'] == '2000ml cream dairy farmers full milk'

    def test_no_barcode_field_absent_from_output(self):
        product = _first_product(_make_cleaner(DataCleanerColes, [_COLES_BASE]))
        assert 'barcode' not in product

    def test_price_hash_is_present_and_is_string(self):
        product = _first_product(_make_cleaner(DataCleanerColes, [_COLES_BASE]))
        assert isinstance(product.get('price_hash'), str)


# ---------------------------------------------------------------------------
# IGA
# ---------------------------------------------------------------------------

_IGA_BASE = {
    'productId': 'P001',
    'name': 'Full Cream Milk',
    'brand': 'Dairy Farmers',
    'barcode': '9310088000010',
    'priceNumeric': 3.20,
    'wasWholePrice': None,
    'tprPrice': [],
    'pricePerUnit': '$1.60 per 1L',
    'unitOfSize': {'size': 2, 'abbreviation': 'l'},
    'unitOfMeasure': {'size': 1, 'abbreviation': 'l'},
    'sellBy': 'Each',
    'available': True,
    'defaultCategory': [{'categoryBreadcrumb': 'Dairy/Milk/Full Cream'}],
}


class TestIgaNormalization:
    def test_size_l_converted_to_ml(self):
        product = _first_product(_make_cleaner(DataCleanerIga, [_IGA_BASE]))
        assert '2000ml' in product['sizes']

    def test_grams_size_kept_as_grams(self):
        raw = {
            **_IGA_BASE,
            'unitOfSize': {'size': 200, 'abbreviation': 'g'},
            'unitOfMeasure': {'size': 100, 'abbreviation': 'g'},
        }
        product = _first_product(_make_cleaner(DataCleanerIga, [raw]))
        assert '200g' in product['sizes']

    def test_normalized_brand_is_cleaned_lowercase(self):
        product = _first_product(_make_cleaner(DataCleanerIga, [_IGA_BASE]))
        assert product['normalized_brand'] == 'dairy farmers'

    def test_normalized_name_brand_size_is_sorted_bag_of_words(self):
        product = _first_product(_make_cleaner(DataCleanerIga, [_IGA_BASE]))
        assert product['normalized_name_brand_size'] == '2000ml cream dairy farmers full milk'

    def test_valid_barcode_preserved(self):
        product = _first_product(_make_cleaner(DataCleanerIga, [_IGA_BASE]))
        assert product['barcode'] == '9310088000010'

    def test_price_hash_is_present_and_is_string(self):
        product = _first_product(_make_cleaner(DataCleanerIga, [_IGA_BASE]))
        assert isinstance(product.get('price_hash'), str)


# ---------------------------------------------------------------------------
# Aldi
# ---------------------------------------------------------------------------

_ALDI_BASE = {
    'sku': 'A12345',
    'name': 'Full Cream Milk',
    'brandName': 'Dairy Farmers',
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


class TestAldiNormalization:
    def test_size_l_converted_to_ml(self):
        product = _first_product(_make_cleaner(DataCleanerAldi, [_ALDI_BASE]))
        assert product['sizes'] == ['2000ml']

    def test_kg_size_converted_to_grams(self):
        raw = {**_ALDI_BASE, 'sellingSize': '0.5kg'}
        product = _first_product(_make_cleaner(DataCleanerAldi, [raw]))
        assert '500g' in product['sizes']

    def test_normalized_brand_is_cleaned_lowercase(self):
        product = _first_product(_make_cleaner(DataCleanerAldi, [_ALDI_BASE]))
        assert product['normalized_brand'] == 'dairy farmers'

    def test_no_brand_means_no_normalized_brand_field(self):
        raw = {**_ALDI_BASE, 'brandName': None}
        product = _first_product(_make_cleaner(DataCleanerAldi, [raw]))
        assert 'normalized_brand' not in product

    def test_normalized_name_brand_size_is_sorted_bag_of_words(self):
        product = _first_product(_make_cleaner(DataCleanerAldi, [_ALDI_BASE]))
        assert product['normalized_name_brand_size'] == '2000ml cream dairy farmers full milk'

    def test_price_hash_is_present_and_is_string(self):
        product = _first_product(_make_cleaner(DataCleanerAldi, [_ALDI_BASE]))
        assert isinstance(product.get('price_hash'), str)


# ---------------------------------------------------------------------------
# Cross-store: same product, different raw formats → identical normalized key
# ---------------------------------------------------------------------------

class TestCrossStoreNormalizedKey:
    """
    The same logical product run through four different store cleaners should
    produce an identical normalized_name_brand_size key. This is the core
    value proposition of the normalization pipeline — cross-store deduplication.
    """

    _WOW_MILK = {
        'Stockcode': 1,
        'Name': 'Full Cream Milk',
        'Brand': 'Dairy Farmers',
        'Barcode': None,
        'PackageSize': '2L',
        'UrlFriendlyName': 'full-cream-milk',
        'Price': 3.20,
        'WasPrice': None,
        'CupString': None,
        'InstoreCupPrice': None,
        'CupMeasure': None,
        'Rating': {'Average': None, 'ReviewCount': None},
        'AdditionalAttributes': {},
        'IsAvailable': True,
    }

    _COLES_MILK = {
        '_type': 'PRODUCT',
        'id': '99',
        'name': 'Full Cream Milk',
        'brand': 'Dairy Farmers',
        'barcode': None,
        'size': '2L',
        'pricing': {
            'now': 3.20,
            'was': 0,
            'comparable': None,
            'unit': {'price': None, 'ofMeasureUnits': None},
        },
        'onlineHeirs': [],
    }

    _IGA_MILK = {
        'productId': 'P1',
        'name': 'Full Cream Milk',
        'brand': 'Dairy Farmers',
        'barcode': None,
        'priceNumeric': 3.20,
        'wasWholePrice': None,
        'tprPrice': [],
        'pricePerUnit': None,
        'unitOfSize': {'size': 2, 'abbreviation': 'l'},
        'unitOfMeasure': {'size': 1, 'abbreviation': 'l'},
        'sellBy': 'Each',
        'available': True,
        'defaultCategory': [{'categoryBreadcrumb': ''}],
    }

    _ALDI_MILK = {
        'sku': 'A1',
        'name': 'Full Cream Milk',
        'brandName': 'Dairy Farmers',
        'sellingSize': '2L',
        'urlSlugText': 'full-cream-milk',
        'assets': [],
        'categories': [],
        'price': {
            'amount': 320,
            'wasPriceDisplay': None,
            'comparisonDisplay': None,
            'comparison': None,
        },
        'notForSale': False,
    }

    def _get_key(self, cls, raw):
        return _first_product(_make_cleaner(cls, [raw]))['normalized_name_brand_size']

    def test_woolworths_and_coles_produce_same_key(self):
        assert self._get_key(DataCleanerWoolworths, self._WOW_MILK) == \
               self._get_key(DataCleanerColes, self._COLES_MILK)

    def test_woolworths_and_iga_produce_same_key(self):
        assert self._get_key(DataCleanerWoolworths, self._WOW_MILK) == \
               self._get_key(DataCleanerIga, self._IGA_MILK)

    def test_all_four_stores_produce_same_key(self):
        wow = self._get_key(DataCleanerWoolworths, self._WOW_MILK)
        col = self._get_key(DataCleanerColes, self._COLES_MILK)
        iga = self._get_key(DataCleanerIga, self._IGA_MILK)
        aldi = self._get_key(DataCleanerAldi, self._ALDI_MILK)
        assert wow == col == iga == aldi
