import pytest
from datetime import datetime
from scraping.utils.product_scraping_utils.DataCleanerIga import DataCleanerIga


@pytest.fixture
def cleaner():
    return DataCleanerIga(
        raw_product_list=[],
        company='IGA',
        store_name='IGA Test',
        store_id='IGA001',
        state='nsw',
        timestamp=datetime(2024, 6, 15),
        brand_translations={},
        product_translations={}
    )


RAW_PRODUCT_REGULAR = {
    'productId': 'P001',
    'name': 'Full Cream Milk',
    'brand': 'Pura',
    'barcode': '9310088000027',
    'description': 'Fresh milk',
    'priceNumeric': 2.80,
    'wasWholePrice': None,
    'tprPrice': [],
    'pricePerUnit': '$1.40 per 1L',
    'unitOfSize': {'size': 2, 'abbreviation': 'l'},
    'unitOfMeasure': {'size': 1, 'abbreviation': 'l'},
    'sellBy': 'Each',
    'available': True,
    'defaultCategory': [{'categoryBreadcrumb': 'Dairy/Milk/Full Cream'}],
}

RAW_PRODUCT_ON_SPECIAL = {
    'productId': 'P002',
    'name': 'Cheese Block',
    'brand': 'Bega',
    'barcode': None,
    'description': '',
    'priceNumeric': 5.00,
    'wasWholePrice': 7.00,
    'tprPrice': [{'wholePrice': 5.00}],
    'pricePerUnit': '$25.00 per 1kg',
    'unitOfSize': {'size': 200, 'abbreviation': 'g'},
    'unitOfMeasure': {'size': 100, 'abbreviation': 'g'},
    'sellBy': 'Each',
    'available': True,
    'defaultCategory': [{'categoryBreadcrumb': 'Dairy/Cheese'}],
}


class TestTransformProductPrice:
    def test_regular_price_not_on_special(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result['price_current'] == 2.80
        assert result['is_on_special'] is False

    def test_special_price_taken_from_tpr(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result['price_current'] == 5.00
        assert result['price_was'] == 7.00
        assert result['is_on_special'] is True
        assert result['price_save_amount'] == 2.00


class TestTransformProductSize:
    def test_size_string_constructed_from_unit_of_size(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result['size'] == '2l'

    def test_sell_by_each_not_appended_to_size(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert 'Each' not in result['size']

    def test_sell_by_non_each_appended_to_size(self, cleaner):
        raw = {**RAW_PRODUCT_REGULAR, 'sellBy': 'Dozen'}
        result = cleaner._transform_product(raw)
        assert 'Dozen' in result['size']

    def test_size_grams(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result['size'] == '200g'


class TestTransformProductCategoryPath:
    def test_category_split_from_breadcrumb_slash(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert 'Dairy' in result['category_path']
        assert 'Milk' in result['category_path']
        assert 'Full Cream' in result['category_path']

    def test_empty_breadcrumb_gives_empty_path(self, cleaner):
        raw = {**RAW_PRODUCT_REGULAR, 'defaultCategory': [{'categoryBreadcrumb': ''}]}
        result = cleaner._transform_product(raw)
        assert result['category_path'] == []


class TestTransformProductAvailability:
    def test_available_true(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result['is_available'] is True

    def test_available_false(self, cleaner):
        raw = {**RAW_PRODUCT_REGULAR, 'available': False}
        result = cleaner._transform_product(raw)
        assert result['is_available'] is False


class TestTransformProductUnitPrice:
    def test_unit_price_calculated_numerically(self, cleaner):
        # price=2.80, measure_size=1, product_size=2 → 2.80*(1/2)=1.40
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result.get('per_unit_price_value') == pytest.approx(1.40)

    def test_unit_price_standardized_to_per_1l(self, cleaner):
        result = cleaner._transform_product(RAW_PRODUCT_REGULAR)
        assert result.get('unit_of_measure') == '1l'
        assert result.get('unit_price') == pytest.approx(1.40)

    def test_unit_price_per_1kg_for_grams_product(self, cleaner):
        # price=5.00, measure_size=100, product_size=200 → 5.00*(100/200)=2.50 per 100g → 25.00 per kg
        result = cleaner._transform_product(RAW_PRODUCT_ON_SPECIAL)
        assert result.get('unit_of_measure') == '1kg'
        assert result.get('unit_price') == pytest.approx(25.00)
