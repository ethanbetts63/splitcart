import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerWoolworths import StoreCleanerWoolworths


RAW_STORE_API1 = {
    'StoreNo': '1001',
    'Name': 'Woolworths Sydney',
    'Division': 'Woolworths',
    'Phone': '0298888888',
    'AddressLine1': '123 George St',
    'Suburb': 'Sydney',
    'State': 'NSW',
    'Postcode': '2000',
    'Latitude': -33.87,
    'Longitude': 151.21,
    'TradingHours': {},
    'Facilities': [],
    'IsOpen': True,
}

RAW_STORE_API2 = {
    'FulfilmentStoreId': '2001',
    'Description': 'Woolworths Parramatta',
    'Street1': '100 Church St',
    'Street2': None,
    'Suburb': 'Parramatta',
    'Postcode': '2150',
    'FulfilmentDeliveryMethods': ['Delivery'],
}


class TestApiFormatDetection:
    def test_api1_detected_by_store_no(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API1, 'Woolworths', datetime(2024, 6, 15))
        assert cleaner.api_format == 1

    def test_api2_detected_by_fulfilment_store_id(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API2, 'Woolworths', datetime(2024, 6, 15))
        assert cleaner.api_format == 2

    def test_unknown_format_returns_zero(self):
        cleaner = StoreCleanerWoolworths({}, 'Woolworths', datetime(2024, 6, 15))
        assert cleaner.api_format == 0


class TestTransformStoreApi1:
    def test_store_id_mapped(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API1, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_id'] == '1001'

    def test_is_active_set_true(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API1, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['is_active'] is True

    def test_postcode_cleaned(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API1, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['postcode'] == '2000'

    def test_na_store_name_replaced_with_suburb(self):
        raw = {**RAW_STORE_API1, 'Name': 'N/A', 'Suburb': 'Newtown'}
        cleaner = StoreCleanerWoolworths(raw, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_name'] == 'Newtown'

    def test_real_store_name_kept(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API1, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_name'] == 'Woolworths Sydney'


class TestTransformStoreApi2:
    def test_store_id_mapped(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API2, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_id'] == '2001'

    def test_store_name_mapped(self):
        cleaner = StoreCleanerWoolworths(RAW_STORE_API2, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['store_name'] == 'Woolworths Parramatta'


class TestTransformStoreUnknownFormat:
    def test_unknown_format_returns_empty_dict(self):
        cleaner = StoreCleanerWoolworths({}, 'Woolworths', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result == {}
