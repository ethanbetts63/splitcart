
from django.test import TestCase
from datetime import datetime
from api.utils.shop_scraping_utils.iga.clean_raw_store_data_iga import clean_raw_store_data_iga

class TestCleanRawStoreDataIga(TestCase):

    def setUp(self):
        self.timestamp = datetime.now()
        self.raw_store_data = {
            "storeId": 123,
            "storeName": "IGA Test Store",
            "retailerStoreId": "R123",
            "email": "test@iga.com",
            "phone": "0212345678",
            "address": "1 Test Street",
            "suburb": "Testville",
            "state": "NSW",
            "postcode": "2000",
            "latitude": -33.86,
            "longitude": 151.20,
            "hours": "Mon-Fri: 8am-8pm",
            "onlineShopUrl": "https://shop.iga.com.au/",
            "storeUrl": "/test-store",
            "ecommerceUrl": "/shop",
            "id": "rec123",
            "status": "Open",
            "type": "Supermarket",
            "siteId": "S123",
            
            "shoppingModes": ["InStore"]
        }

    def test_clean_raw_store_data(self):
        cleaned_data = clean_raw_store_data_iga(self.raw_store_data, "iga", self.timestamp)

        self.assertEqual(cleaned_data['metadata']['company'], "iga")
        self.assertEqual(cleaned_data['metadata']['scraped_at'], self.timestamp.isoformat())

        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "IGA Test Store")
        self.assertEqual(store_data['store_id'], 123)
        self.assertEqual(store_data['retailer_store_id'], "R123")
        self.assertEqual(store_data['email'], "test@iga.com")
        self.assertEqual(store_data['phone_number'], "0212345678")
        self.assertEqual(store_data['address_line_1'], "1 Test Street")
        self.assertEqual(store_data['suburb'], "Testville")
        self.assertEqual(store_data['state'], "NSW")
        self.assertEqual(store_data['postcode'], "2000")
        self.assertEqual(store_data['latitude'], -33.86)
        self.assertEqual(store_data['longitude'], 151.20)
        self.assertEqual(store_data['trading_hours'], "Mon-Fri: 8am-8pm")
        self.assertEqual(store_data['online_shop_url'], "https://shop.iga.com.au/")
        self.assertEqual(store_data['store_url'], "/test-store")
        self.assertEqual(store_data['ecommerce_url'], "/shop")
        self.assertEqual(store_data['record_id'], "rec123")
        self.assertEqual(store_data['status'], "Open")
        self.assertEqual(store_data['store_type'], "Supermarket")
        self.assertEqual(store_data['site_id'], "S123")
        
        self.assertEqual(store_data['shopping_modes'], ["InStore"])

    def test_missing_data(self):
        raw_data = {"storeId": 456, "storeName": "Incomplete IGA"}
        cleaned_data = clean_raw_store_data_iga(raw_data, "iga", self.timestamp)
        store_data = cleaned_data['store_data']
        self.assertEqual(store_data['name'], "Incomplete IGA")
        self.assertEqual(store_data['store_id'], 456)
        self.assertIsNone(store_data['retailer_store_id'])
        self.assertIsNone(store_data['email'])
