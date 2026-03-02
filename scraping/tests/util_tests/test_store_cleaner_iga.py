import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerIga import StoreCleanerIga


RAW_STORE = {
    'storeId': 'IGA001',
    'tag': 'iga-sydney',
    'storeName': 'IGA Sydney',
    'email': 'sydney@iga.com.au',
    'phone': '0212345678',
    'address': '123 Pitt St',
    'suburb': 'Sydney',
    'state': 'NSW',
    'postcode': '2000',
    'latitude': -33.87,
    'longitude': 151.21,
    'hours': {'mon': '7am-10pm'},
    'onlineShopUrl': 'https://shop.iga.com.au',
    'storeUrl': 'https://www.iga.com.au/stores/sydney',
    'ecommerceUrl': 'https://ecommerce.iga.com.au',
    'id': 'REC001',
    'status': 'active',
    'type': 'supermarket',
    'siteId': 'SITE001',
    'shoppingModes': ['instore', 'online'],
}


@pytest.fixture
def cleaner():
    return StoreCleanerIga(RAW_STORE, 'IGA', datetime(2024, 6, 15))


class TestTransformStore:
    def test_store_id_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_id'] == 'IGA001'

    def test_store_name_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_name'] == 'IGA Sydney'

    def test_postcode_cleaned(self, cleaner):
        result = cleaner._transform_store()
        assert result['postcode'] == '2000'

    def test_3_digit_postcode_padded(self):
        raw = {**RAW_STORE, 'postcode': '800'}
        cleaner = StoreCleanerIga(raw, 'IGA', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['postcode'] == '0800'

    def test_is_active_always_true(self, cleaner):
        result = cleaner._transform_store()
        assert result['is_active'] is True

    def test_state_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['state'] == 'NSW'

    def test_suburb_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['suburb'] == 'Sydney'
