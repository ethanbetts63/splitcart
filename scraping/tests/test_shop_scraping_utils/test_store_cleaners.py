from django.test import TestCase
from datetime import datetime
from scraping.utils.shop_scraping_utils.StoreCleanerWoolworths import StoreCleanerWoolworths
from scraping.utils.shop_scraping_utils.StoreCleanerColes import StoreCleanerColes
from scraping.utils.shop_scraping_utils.StoreCleanerAldi import StoreCleanerAldi
from scraping.utils.shop_scraping_utils.StoreCleanerIga import StoreCleanerIga

class TestStoreCleanerWoolworths(TestCase):

    def setUp(self):
        self.company = "woolworths"
        self.timestamp = datetime.now()

    def test_cleaner_with_api1_format(self):
        """Test that the cleaner correctly processes data from the StoreLocator data_management."""
        raw_data_api1 = {
            "StoreNo": 1234,
            "Name": "Woolworths Town Hall",
            "Division": "SUPERMARKETS",
            "Phone": "0298765432",
            "AddressLine1": "123 George St",
            "AddressLine2": "",
            "Suburb": "Sydney",
            "State": "NSW",
            "Postcode": "2000",
            "Latitude": -33.87, 
            "Longitude": 151.20,
            "TradingHours": "Mon-Fri: 7am-10pm",
            "Facilities": ["Bakery", "Deli"],
            "IsOpen": True
        }

        cleaner = StoreCleanerWoolworths(raw_data_api1, self.company, self.timestamp)
        cleaned_output = cleaner.clean()

        # Check metadata
        self.assertEqual(cleaned_output['metadata']['company'], self.company)

        # Check store data
        store_data = cleaned_output['store_data']
        self.assertEqual(store_data['store_id'], 1234)
        self.assertEqual(store_data['store_name'], "Woolworths Town Hall")
        self.assertEqual(store_data['division'], "SUPERMARKETS")
        self.assertEqual(store_data['address_line_1'], "123 George St")
        self.assertEqual(store_data['postcode'], "2000")
        self.assertTrue(store_data['is_active'])
        self.assertTrue(store_data['is_trading'])

    def test_cleaner_with_api2_format(self):
        """Test that the cleaner correctly processes data from the fulfilment/stores data_management."""
        raw_data_api2 = {
            "FulfilmentStoreId": "5678",
            "Description": "Woolworths Metro Central",
            "Street1": "456 Pitt St",
            "Street2": "Shop 3",
            "Suburb": "Sydney",
            "Postcode": "2000",
            "FulfilmentDeliveryMethods": ["Pickup", "DriveUp"]
        }

        cleaner = StoreCleanerWoolworths(raw_data_api2, self.company, self.timestamp)
        cleaned_output = cleaner.clean()

        # Check metadata
        self.assertEqual(cleaned_output['metadata']['company'], self.company)

        # Check store data
        store_data = cleaned_output['store_data']
        self.assertEqual(store_data['store_id'], "5678")
        self.assertEqual(store_data['retailer_store_id'], "5678")
        self.assertEqual(store_data['store_name'], "Woolworths Metro Central")
        self.assertEqual(store_data['address_line_1'], "456 Pitt St")
        self.assertEqual(store_data['shopping_modes'], ["Pickup", "DriveUp"])
        self.assertIsNone(store_data.get('division')) # Division is not present in data_management 2
        self.assertTrue(store_data['is_active'])

    def test_cleaner_with_unknown_format(self):
        """Test that the cleaner handles an unknown data format gracefully."""
        raw_data_unknown = {"some_other_key": "some_value"}

        cleaner = StoreCleanerWoolworths(raw_data_unknown, self.company, self.timestamp)
        cleaned_output = cleaner.clean()

        store_data = cleaned_output['store_data']
        self.assertEqual(store_data, {})


class TestStoreCleanerColes(TestCase):

    def setUp(self):
        self.company = "coles"
        self.timestamp = datetime.now()

    def test_cleaner_with_standard_data(self):
        """Test that the cleaner correctly processes a standard store."""
        raw_data = {
            "id": "COL:0432",
            "name": "Coles Central",
            "phone": "0398765432",
            "address": {
                "addressLine": "236 Bourke St",
                "suburb": "Melbourne",
                "state": "VIC",
                "postcode": "3000"
            },
            "position": {
                "latitude": -37.81,
                "longitude": 144.96
            },
            "isTrading": True,
            "brand": {"id": "COL"}
        }

        cleaner = StoreCleanerColes(raw_data, self.company, self.timestamp)
        cleaned_output = cleaner.clean()

        # Check metadata
        self.assertEqual(cleaned_output['metadata']['company'], self.company)
        
        # Check store data
        store_data = cleaned_output['store_data']
        self.assertEqual(store_data['store_id'], "COL:0432")
        self.assertEqual(store_data['store_name'], "Coles Central")
        self.assertEqual(store_data['division'], "Coles Supermarkets")
        self.assertEqual(store_data['suburb'], "Melbourne")
        self.assertTrue(store_data['is_trading'])

    def test_cleaner_handles_na_name(self):
        """Test that a store with a name of 'N/A' is given a constructed name."""
        raw_data = {
            "id": "LQR:8561",
            "name": "N/A",
            "address": {
                "suburb": "Richmond"
            },
            "position": {},
            "brand": {"id": "LQR"}
        }

        cleaner = StoreCleanerColes(raw_data, self.company, self.timestamp)
        cleaned_output = cleaner.clean()
        store_data = cleaned_output['store_data']

        self.assertEqual(store_data['store_name'], "Liquorland Richmond")
        self.assertEqual(store_data['division'], "Liquorland")


class TestStoreCleanerAldi(TestCase):

    def setUp(self):
        self.company = "aldi"
        self.timestamp = datetime.now()

    def test_cleaner_with_standard_data(self):
        """Test that the cleaner correctly processes a standard store."""
        raw_data = {
            "id": "ALDI-123",
            "name": "ALDI Preston",
            "publicPhoneNumber": "0312345678",
            "address": {
                "address1": "123 High St",
                "address2": "Preston Market",
                "city": "Preston",
                "regionName": "VIC",
                "zipCode": "3072",
                "latitude": -37.74,
                "longitude": 145.00
            },
            "isOpenNow": False,
            "facilities": ["Parking"],
            "availableCustomerServiceTypes": ["Returns"],
            "alcoholAvailability": ["Beer", "Wine"]
        }

        cleaner = StoreCleanerAldi(raw_data, self.company, self.timestamp)
        cleaned_output = cleaner.clean()
        store_data = cleaned_output['store_data']

        self.assertEqual(store_data['store_id'], "ALDI-123")
        self.assertEqual(store_data['store_name'], "ALDI Preston")
        self.assertEqual(store_data['suburb'], "Preston")
        self.assertEqual(store_data['state'], "VIC")
        self.assertFalse(store_data['is_trading'])
        self.assertEqual(store_data['facilities'], ["Parking"])


class TestStoreCleanerIga(TestCase):

    def setUp(self):
        self.company = "iga"
        self.timestamp = datetime.now()

    def test_cleaner_with_standard_data(self):
        """Test that the cleaner correctly processes a standard store."""
        raw_data = {
            "storeId": 987,
            "tag": "IGA-987-Tag",
            "storeName": "IGA Express",
            "email": "contact@iga.com",
            "phone": "0899998888",
            "address": "456 Flinders St",
            "suburb": "Perth",
            "state": "WA",
            "postcode": "6000",
            "latitude": -31.95,
            "longitude": 115.86,
            "hours": "Every day 8am-9pm",
            "onlineShopUrl": "https://shop.iga.com.au",
            "storeUrl": "https://iga.com.au/perth",
            "ecommerceUrl": "https://ecom.iga.com.au",
            "id": "rec-123",
            "status": "Active",
            "type": "Supermarket",
            "siteId": "site-456",
            "shoppingModes": ["InStore"]
        }

        cleaner = StoreCleanerIga(raw_data, self.company, self.timestamp)
        cleaned_output = cleaner.clean()
        store_data = cleaned_output['store_data']

        self.assertEqual(store_data['store_id'], 987)
        self.assertEqual(store_data['retailer_store_id'], "IGA-987-Tag")
        self.assertEqual(store_data['store_name'], "IGA Express")
        self.assertEqual(store_data['suburb'], "Perth")
        self.assertEqual(store_data['online_shop_url'], "https://shop.iga.com.au")
