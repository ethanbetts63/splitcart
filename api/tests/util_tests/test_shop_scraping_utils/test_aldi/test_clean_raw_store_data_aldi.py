
from django.test import TestCase
from datetime import datetime
from api.utils.shop_scraping_utils.aldi.clean_raw_store_data_aldi import clean_raw_store_data_aldi

class CleanRawStoreDataAldiTest(TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.raw_store_data = {
            "id": "12345",
            "name": "Aldi Test Store",
            "publicPhoneNumber": "0812345678",
            "address": {
                "address1": "123 Test St",
                "address2": "Unit 1",
                "city": "Testville",
                "regionName": "WA",
                "zipCode": "6000",
                "latitude": -31.95,
                "longitude": 115.86
            },
            "facilities": ["Parking", "Trolleys"],
            "isOpenNow": True,
            "availableCustomerServiceTypes": ["Phone"],
            "alcoholAvailability": ["Beer", "Wine"]
        }

    def test_clean_raw_store_data_complete(self):
        """Test with a complete raw store data dictionary."""
        cleaned_data = clean_raw_store_data_aldi(self.raw_store_data, "aldi", self.timestamp)

        self.assertEqual(cleaned_data['metadata']['company'], "aldi")
        self.assertEqual(cleaned_data['metadata']['scraped_at'], self.timestamp.isoformat())

        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Aldi Test Store")
        self.assertEqual(store_data['store_id'], "12345")
        self.assertIsNone(store_data['retailer_store_id'])
        self.assertTrue(store_data['is_active'])
        self.assertIsNone(store_data['division'])
        self.assertIsNone(store_data['email'])
        self.assertEqual(store_data['phone_number'], "0812345678")
        self.assertEqual(store_data['address_line_1'], "123 Test St")
        self.assertEqual(store_data['address_line_2'], "Unit 1")
        self.assertEqual(store_data['suburb'], "Testville")
        self.assertEqual(store_data['state'], "WA")
        self.assertEqual(store_data['postcode'], "6000")
        self.assertEqual(store_data['latitude'], -31.95)
        self.assertEqual(store_data['longitude'], 115.86)
        self.assertIsNone(store_data['trading_hours'])
        self.assertEqual(store_data['facilities'], ["Parking", "Trolleys"])
        self.assertTrue(store_data['is_trading'])
        self.assertIsNone(store_data['online_shop_url'])
        self.assertIsNone(store_data['store_url'])
        self.assertIsNone(store_data['ecommerce_url'])
        self.assertIsNone(store_data['record_id'])
        self.assertIsNone(store_data['status'])
        self.assertIsNone(store_data['store_type'])
        self.assertIsNone(store_data['site_id'])
        self.assertIsNone(store_data['category_hierarchy_id'])
        self.assertIsNone(store_data['shopping_modes'])
        self.assertEqual(store_data['available_customer_service_types'], ["Phone"])
        self.assertEqual(store_data['alcohol_availability'], ["Beer", "Wine"])

    def test_clean_raw_store_data_missing_fields(self):
        """Test with missing optional fields."""
        raw_data_missing = {
            "id": "67890",
            "name": "Aldi Minimal Store",
            "address": {
                "city": "Minimalville",
                "regionName": "VIC"
            },
            "isOpenNow": False
        }
        cleaned_data = clean_raw_store_data_aldi(raw_data_missing, "aldi", self.timestamp)

        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Aldi Minimal Store")
        self.assertEqual(store_data['store_id'], "67890")
        self.assertIsNone(store_data['phone_number'])
        self.assertIsNone(store_data['address_line_1'])
        self.assertEqual(store_data['suburb'], "Minimalville")
        self.assertEqual(store_data['state'], "VIC")
        self.assertIsNone(store_data['postcode'])
        self.assertFalse(store_data['is_trading'])
        self.assertIsNone(store_data['facilities'])
        self.assertIsNone(store_data['available_customer_service_types'])
        self.assertIsNone(store_data['alcohol_availability'])

    def test_clean_raw_store_data_empty(self):
        """Test with an empty raw store data dictionary."""
        cleaned_data = clean_raw_store_data_aldi({}, "aldi", self.timestamp)

        store_data = cleaned_data['store_data']
        self.assertIsNone(store_data['name'])
        self.assertIsNone(store_data['store_id'])
        self.assertIsNone(store_data['phone_number'])
        self.assertIsNone(store_data['address_line_1'])
        self.assertIsNone(store_data['suburb'])
        self.assertIsNone(store_data['state'])
        self.assertIsNone(store_data['postcode'])
        self.assertIsNone(store_data['latitude'])
        self.assertIsNone(store_data['longitude'])
        self.assertIsNone(store_data['facilities'])
        self.assertIsNone(store_data['is_trading'])

    def test_clean_raw_store_data_no_address(self):
        """Test with raw data missing the 'address' key."""
        raw_data_no_address = {
            "id": "999",
            "name": "Aldi No Address",
            "publicPhoneNumber": "0898765432",
            "isOpenNow": True
        }
        cleaned_data = clean_raw_store_data_aldi(raw_data_no_address, "aldi", self.timestamp)

        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Aldi No Address")
        self.assertIsNone(store_data['address_line_1'])
        self.assertIsNone(store_data['suburb'])
        self.assertIsNone(store_data['state'])
