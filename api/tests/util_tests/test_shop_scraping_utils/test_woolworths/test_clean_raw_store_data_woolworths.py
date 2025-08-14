
from django.test import TestCase
from datetime import datetime
from api.utils.shop_scraping_utils.woolworths.clean_raw_store_data_woolworths import clean_raw_store_data_woolworths

class TestCleanRawStoreDataWoolworths(TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.raw_store_data = {
            "StoreNo": 1234,
            "Name": "Woolworths Metro",
            "Division": "Woolworths",
            "Phone": "0298765432",
            "AddressLine1": "1 Main Street",
            "AddressLine2": "",
            "Suburb": "Sydney",
            "State": "NSW",
            "Postcode": "2000",
            "Latitude": -33.86,
            "Longitude": 151.20,
            "TradingHours": "Mon-Fri: 7am-10pm",
            "Facilities": "Parking, Bakery",
            "IsOpen": True
        }

    def test_clean_raw_store_data(self):
        cleaned_data = clean_raw_store_data_woolworths(self.raw_store_data, "woolworths", self.timestamp)

        self.assertEqual(cleaned_data['metadata']['company'], "woolworths")
        self.assertEqual(cleaned_data['metadata']['scraped_at'], self.timestamp.isoformat())

        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Woolworths Metro")
        self.assertEqual(store_data['store_id'], 1234)
        self.assertEqual(store_data['division'], "Woolworths")
        self.assertEqual(store_data['phone_number'], "0298765432")
        self.assertEqual(store_data['address_line_1'], "1 Main Street")
        self.assertEqual(store_data['suburb'], "Sydney")
        self.assertEqual(store_data['state'], "NSW")
        self.assertEqual(store_data['postcode'], "2000")
        self.assertEqual(store_data['latitude'], -33.86)
        self.assertEqual(store_data['longitude'], 151.20)
        self.assertEqual(store_data['trading_hours'], "Mon-Fri: 7am-10pm")
        self.assertEqual(store_data['facilities'], "Parking, Bakery")
        self.assertTrue(store_data['is_trading'])
        self.assertTrue(store_data['is_active'])

    def test_missing_data(self):
        raw_data = {"StoreNo": 5678, "Name": "Incomplete Store"}
        cleaned_data = clean_raw_store_data_woolworths(raw_data, "woolworths", self.timestamp)
        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Incomplete Store")
        self.assertEqual(store_data['store_id'], 5678)
        self.assertIsNone(store_data['division'])
        self.assertIsNone(store_data['phone_number'])
