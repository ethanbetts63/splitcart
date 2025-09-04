import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock

from decimal import Decimal

from django.test import TestCase, override_settings

from companies.models import Company, Division, Store
from products.models import Product, Price
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory, StoreFactory
from api.utils.scraper_utils.DataCleanerColes import DataCleanerColes
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator

RAW_COLES_PRODUCTS = [
  {
    "_type": "PRODUCT",
    "id": 3942620,
    "name": "Graze Lamb Extra Trim Cutlets",
    "brand": "Coles",
    "description": "COLES GRAZE LAMB EXTRA TRIM CUTLETS 7 X 5",
    "size": "approx. 300g",
    "availability": False,
    "imageUris": [{"uri": "/3/3942620.jpg"}],
    "onlineHeirs": [
      {
        "aisle": "Graze Grass-Fed Lamb",
        "category": "Lamb",
        "subCategory": "Meat & Seafood"
      }
    ],
    "pricing": {
      "now": 12.00,
      "was": 14.10,
      "unit": {"price": 40.00, "ofMeasureUnits": "kg"},
      "comparable": "$40.00 per 1kg",
      "promotionType": "SPECIAL",
      "onlineSpecial": True
    }
  },
  {
    "_type": "PRODUCT",
    "id": 3477123,
    "name": "Tasmanian Smoked Salmon",
    "brand": "Tassal",
    "description": "TASSAL TASMANIAN SMOKED SALMON",
    "size": "250g",
    "availability": True,
    "imageUris": [{"uri": "/3/3477123.jpg"}],
    "onlineHeirs": [
      {
        "aisle": "Smoked And Cured Fish",
        "category": "Seafood",
        "subCategory": "Meat & Seafood"
      }
    ],
    "pricing": {
      "now": 21.00,
      "was": 0,
      "unit": {"price": 84.00, "ofMeasureUnits": "kg"},
      "comparable": "$84.00 per 1kg",
      "onlineSpecial": False
    }
  }
]

@override_settings(DEBUG=True)
class TestDataFlowColes(TestCase):

    def setUp(self):
        self.company = CompanyFactory(name="Coles")
        self.division = DivisionFactory(company=self.company)
        self.store = StoreFactory(company=self.company, division=self.division, store_name="Coles Test Store", store_id="COL:1234")
        self.temp_dir = tempfile.mkdtemp()
        self.inbox_path = self.temp_dir

        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SUCCESS = lambda x: x
        self.mock_command.style.WARNING = lambda x: x
        self.mock_command.style.ERROR = lambda x: x
        self.mock_command.style.SQL_FIELD = lambda x: x

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_coles_data_flow_from_inbox(self):
        # --- Stage 1: Create a realistic inbox file ---
        timestamp = datetime.now()
        cleaner = DataCleanerColes(
            raw_product_list=RAW_COLES_PRODUCTS,
            company=self.company.name,
            store_id=self.store.store_id,
            store_name=self.store.store_name,
            state=self.store.state,
            timestamp=timestamp
        )
        cleaned_data_packet = cleaner.clean_data()

        inbox_file_path = os.path.join(self.inbox_path, "coles_test.jsonl")
        with open(inbox_file_path, 'w') as f:
            for product in cleaned_data_packet['products']:
                line_data = {"product": product, "metadata": cleaned_data_packet['metadata']}
                json.dump(line_data, f)
                f.write('\n')

        # --- Stage 2: Update Database ---
        orchestrator = UpdateOrchestrator(self.mock_command, self.inbox_path)
        orchestrator.run()

        # --- Stage 3: Assert Database State ---
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Price.objects.count(), 2)

        # Product 1: Lamb Cutlets
        product1 = Product.objects.get(name="Graze Lamb Extra Trim Cutlets")
        self.assertEqual(product1.brand, "Coles")
        self.assertEqual(product1.sizes, ["300g"])
        
        price1 = Price.objects.get(product=product1)
        self.assertEqual(price1.store, self.store)
        self.assertEqual(price1.price, Decimal('12.00'))
        self.assertTrue(price1.is_on_special)
        self.assertFalse(price1.is_available)

        # Product 2: Smoked Salmon
        product2 = Product.objects.get(name="Tasmanian Smoked Salmon")
        self.assertEqual(product2.brand, "Tassal")
        self.assertEqual(product2.sizes, ["250g"])

        price2 = Price.objects.get(product=product2)
        self.assertEqual(price2.store, self.store)
        self.assertEqual(price2.price, Decimal('21.00'))
        self.assertFalse(price2.is_on_special)
        self.assertTrue(price2.is_available)