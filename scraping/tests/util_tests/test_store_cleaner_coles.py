import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerColes import StoreCleanerColes


RAW_STORE = {
    'id': 'COL:001',
    'name': 'Coles Sydney',
    'phone': '0299999999',
    'address': {
        'addressLine': '123 George St',
        'suburb': 'Sydney',
        'state': 'NSW',
        'postcode': '2000',
    },
    'position': {'latitude': -33.87, 'longitude': 151.21},
    'isTrading': True,
}


@pytest.fixture
def cleaner():
    return StoreCleanerColes(RAW_STORE, 'Coles', datetime(2024, 6, 15))


class TestTransformStoreDivision:
    def test_col_prefix_maps_to_coles_supermarkets(self, cleaner):
        result = cleaner._transform_store()
        assert result['division'] == 'Coles Supermarkets'

    def test_vin_prefix_maps_to_vintage_cellars(self):
        raw = {**RAW_STORE, 'id': 'VIN:001'}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['division'] == 'Vintage Cellars'

    def test_lqr_prefix_maps_to_liquorland(self):
        raw = {**RAW_STORE, 'id': 'LQR:001'}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['division'] == 'Liquorland'

    def test_unknown_prefix_gives_none_division(self):
        raw = {**RAW_STORE, 'id': 'UNK:001'}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['division'] is None


class TestTransformStorePostcode:
    def test_postcode_cleaned(self, cleaner):
        result = cleaner._transform_store()
        assert result['postcode'] == '2000'

    def test_3_digit_postcode_padded(self):
        raw = {**RAW_STORE, 'address': {**RAW_STORE['address'], 'postcode': '800'}}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['postcode'] == '0800'


class TestTransformStoreNameFallback:
    def test_na_name_replaced_with_suburb_for_col(self):
        raw = {**RAW_STORE, 'name': 'N/A', 'id': 'COL:002'}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_name'] == 'Coles Sydney'

    def test_na_name_replaced_with_suburb_for_vin(self):
        raw = {**RAW_STORE, 'name': 'N/A', 'id': 'VIN:001'}
        cleaner = StoreCleanerColes(raw, 'Coles', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_name'] == 'Vintage Cellars Sydney'

    def test_real_name_kept_as_is(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_name'] == 'Coles Sydney'


class TestTransformStoreIsActive:
    def test_is_active_always_true(self, cleaner):
        result = cleaner._transform_store()
        assert result['is_active'] is True
