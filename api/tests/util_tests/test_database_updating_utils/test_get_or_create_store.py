from django.test import TestCase
from companies.models import Store
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory
from api.utils.database_updating_utils.get_or_create_store import get_or_create_store

class GetOrCreateStoreTest(TestCase):

    def test_create_new_store(self):
        """Test that a new store is created if it doesn't exist."""
        company = CompanyFactory()
        store_data = {"name": "New Store", "suburb": "Perth"}
        store, created = get_or_create_store(company, None, "new_store_id", store_data)
        self.assertTrue(created)
        self.assertEqual(store.name, "New Store")
        self.assertEqual(store.suburb, "Perth")
        self.assertEqual(Store.objects.count(), 1)

    def test_get_existing_store(self):
        """Test that an existing store is retrieved and updated."""
        company = CompanyFactory()
        existing_store = Store.objects.create(company=company, store_id="existing_id", name="Old Name", suburb="Old Suburb")
        
        store_data = {"name": "Updated Name", "suburb": "Updated Suburb"}
        store, created = get_or_create_store(company, None, "existing_id", store_data)
        
        self.assertFalse(created)
        self.assertEqual(store.name, "Updated Name")
        self.assertEqual(store.suburb, "Updated Suburb")
        self.assertEqual(Store.objects.count(), 1) # No new store created
        self.assertEqual(store.id, existing_store.id) # Same store updated

    def test_create_store_with_division(self):
        """Test creating a store with an associated division."""
        company = CompanyFactory()
        division = DivisionFactory(company=company)
        store_data = {"name": "Store With Div"}
        store, created = get_or_create_store(company, division, "store_div_id", store_data)
        self.assertTrue(created)
        self.assertEqual(store.division, division)

    def test_update_store_with_division(self):
        """Test updating an existing store to add a division."""
        company = CompanyFactory()
        existing_store = Store.objects.create(company=company, store_id="update_div_id", name="No Div Store")
        division = DivisionFactory(company=company)
        
        store_data = {"name": "Updated Div Store"}
        store, created = get_or_create_store(company, division, "update_div_id", store_data)
        
        self.assertFalse(created)
        self.assertEqual(store.division, division)

    def test_none_values_in_store_data_do_not_overwrite_existing(self):
        """Test that None values in store_data do not overwrite existing non-None values."""
        company = CompanyFactory()
        existing_store = Store.objects.create(
            company=company, 
            store_id="overwrite_test_id", 
            name="Original Name", 
            latitude=10.0, 
            longitude=20.0
        )
        
        store_data = {"name": "New Name", "latitude": None, "longitude": None}
        store, created = get_or_create_store(company, None, "overwrite_test_id", store_data)
        
        self.assertFalse(created)
        self.assertEqual(store.name, "New Name")
        self.assertEqual(store.latitude, 10.0) # Should remain original value
        self.assertEqual(store.longitude, 20.0) # Should remain original value

    def test_store_data_fields_are_updated(self):
        """Test that various fields from store_data are correctly updated."""
        company = CompanyFactory()
        existing_store = Store.objects.create(
            company=company, 
            store_id="update_fields_id", 
            name="Old Name",
            phone_number="123",
            address_line_1="Old Address"
        )
        
        store_data = {
            "name": "New Name",
            "phone_number": "456",
            "address_line_1": "New Address",
            "suburb": "New Suburb",
            "state": "New State",
            "postcode": "New Postcode",
            "latitude": 30.0,
            "longitude": 40.0,
            "trading_hours": {"Mon": "9-5"},
            "facilities": ["Parking"],
            "is_trading": False,
            "retailer_store_id": "R123",
            "email": "test@example.com",
            "online_shop_url": "http://online.com",
            "store_url": "http://store.com",
            "ecommerce_url": "http://ecommerce.com",
            "record_id": "REC1",
            "status": "Open",
            "store_type": "Super",
            "site_id": "SITE1",
            "category_hierarchy_id": "CAT1",
            "shopping_modes": ["Click & Collect"],
            "available_customer_service_types": ["Phone"],
            "alcohol_availability": ["Beer"]
        }
        
        store, created = get_or_create_store(company, None, "update_fields_id", store_data)
        
        self.assertFalse(created)
        self.assertEqual(store.name, "New Name")
        self.assertEqual(store.phone_number, "456")
        self.assertEqual(store.address_line_1, "New Address")
        self.assertEqual(store.suburb, "New Suburb")
        self.assertEqual(store.state, "New State")
        self.assertEqual(store.postcode, "New Postcode")
        self.assertEqual(store.latitude, 30.0)
        self.assertEqual(store.longitude, 40.0)
        self.assertEqual(store.trading_hours, {"Mon": "9-5"})
        self.assertEqual(store.facilities, ["Parking"])
        self.assertEqual(store.is_trading, False)
        self.assertEqual(store.retailer_store_id, "R123")
        self.assertEqual(store.email, "test@example.com")
        self.assertEqual(store.online_shop_url, "http://online.com")
        self.assertEqual(store.store_url, "http://store.com")
        self.assertEqual(store.ecommerce_url, "http://ecommerce.com")
        self.assertEqual(store.record_id, "REC1")
        self.assertEqual(store.status, "Open")
        self.assertEqual(store.store_type, "Super")
        self.assertEqual(store.site_id, "SITE1")
        self.assertEqual(store.category_hierarchy_id, "CAT1")
        self.assertEqual(store.shopping_modes, ["Click & Collect"])
        self.assertEqual(store.available_customer_service_types, ["Phone"])
        self.assertEqual(store.alcohol_availability, ["Beer"])
