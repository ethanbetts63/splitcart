import pytest
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerAldi import StoreCleanerAldi


RAW_STORE = {
    'id': 'ALDI001',
    'name': 'ALDI Sydney',
    'publicPhoneNumber': '0212345678',
    'address': {
        'address1': '123 George St',
        'address2': None,
        'city': 'Sydney',
        'regionName': 'NSW',
        'zipCode': '2000',
        'latitude': -33.87,
        'longitude': 151.21,
    },
    'facilities': ['parking', 'atm'],
    'isOpenNow': True,
    'availableCustomerServiceTypes': ['instore'],
    'alcoholAvailability': 'none',
}


@pytest.fixture
def cleaner():
    return StoreCleanerAldi(RAW_STORE, 'ALDI', datetime(2024, 6, 15))


class TestTransformStore:
    def test_store_id_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_id'] == 'ALDI001'

    def test_store_name_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['store_name'] == 'ALDI Sydney'

    def test_postcode_cleaned(self, cleaner):
        result = cleaner._transform_store()
        assert result['postcode'] == '2000'

    def test_3_digit_postcode_padded(self):
        raw = {**RAW_STORE, 'address': {**RAW_STORE['address'], 'zipCode': '800'}}
        cleaner = StoreCleanerAldi(raw, 'ALDI', datetime(2024, 6, 15))
        result = cleaner._transform_store()
        assert result['postcode'] == '0800'

    def test_is_active_always_true(self, cleaner):
        result = cleaner._transform_store()
        assert result['is_active'] is True

    def test_nested_address_fields_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['suburb'] == 'Sydney'
        assert result['state'] == 'NSW'

    def test_latitude_longitude_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['latitude'] == pytest.approx(-33.87)
        assert result['longitude'] == pytest.approx(151.21)

    def test_facilities_mapped(self, cleaner):
        result = cleaner._transform_store()
        assert result['facilities'] == ['parking', 'atm']
