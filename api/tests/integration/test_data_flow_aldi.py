import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock
from decimal import Decimal
from django.test import TestCase, override_settings
from products.models import Product, Price
from companies.tests.test_helpers.model_factories import CompanyFactory, DivisionFactory, StoreFactory
from api.utils.scraper_utils.DataCleanerAldi import DataCleanerAldi
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator

RAW_ALDI_PRODUCTS = [
  {
    "sku": "000000000000200998",
    "name": "Chocolate Chip Brioche Milk Rolls 8 Pack 280g",
    "brandName": "BON APPETIT",
    "urlSlugText": "bon-appetit-chocolate-chip-brioche-milk-rolls-8-pack-280g",
    "ageRestriction": None,
    "alcohol": None,
    "discontinued": False,
    "discontinuedNote": None,
    "notForSale": True,
    "notForSaleReason": None,
    "quantityMin": 1,
    "quantityMax": 99,
    "quantityInterval": 1,
    "quantityDefault": 1,
    "quantityUnit": "ea",
    "weightType": "0",
    "sellingSize": "280 g",
    "energyClass": None,
    "onSaleDateDisplay": None,
    "price": {
      "amount": 469,
      "amountRelevant": 469,
      "amountRelevantDisplay": "$4.69",
      "bottleDeposit": 0,
      "bottleDepositDisplay": "$0.00",
      "comparison": 168,
      "comparisonDisplay": "$1.68 per 100 g",
      "currencyCode": "AUD",
      "currencySymbol": "$",
      "perUnit": None,
      "perUnitDisplay": None,
      "wasPriceDisplay": None,
      "additionalInfo": None
    },
    "countryExtensions": None,
    "categories": [
      {
        "id": "920000000",
        "name": "Bakery",
        "urlSlugText": "bakery"
      },
      {
        "id": "1111111133",
        "name": "Speciality Breads & Rolls",
        "urlSlugText": "bakery/speciality-breads-rolls"
      }
    ],
    "assets": [
      {
        "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/f2efa456-39e2-4bc9-93c5-5ff8030239f2/{slug}",
        "maxWidth": 1500,
        "maxHeight": 1500,
        "mimeType": "image/*",
        "assetType": "FR01",
        "alt": None,
        "displayName": None
      }
    ],
    "badges": []
  }
]

@override_settings(DEBUG=True)
class TestDataFlowAldi(TestCase):

    def setUp(self):
        self.company = CompanyFactory(name="Aldi")
        self.division = DivisionFactory(company=self.company)
        self.store = StoreFactory(company=self.company, division=self.division, store_name="Aldi Test Store", store_id="ALDI:1234")
        self.temp_dir = tempfile.mkdtemp()
        self.inbox_path = os.path.join(self.temp_dir, 'product_inbox')
        os.makedirs(self.inbox_path, exist_ok=True)

        self.mock_command = Mock()
        self.mock_command.stdout.write = Mock()
        self.mock_command.style.SUCCESS = lambda x: x
        self.mock_command.style.WARNING = lambda x: x
        self.mock_command.style.ERROR = lambda x: x
        self.mock_command.style.SQL_FIELD = lambda x: x

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_aldi_data_flow_from_inbox(self):
        # --- Stage 1: Create a realistic inbox file ---
        timestamp = datetime.now()
        cleaner = DataCleanerAldi(
            raw_product_list=RAW_ALDI_PRODUCTS,
            company=self.company.name,
            store_id=self.store.store_id,
            store_name=self.store.store_name,
            state=self.store.state,
            timestamp=timestamp
        )
        cleaned_data_packet = cleaner.clean_data()

        inbox_file_path = os.path.join(self.inbox_path, "aldi_test.jsonl")
        with open(inbox_file_path, 'w') as f:
            for product in cleaned_data_packet['products']:
                line_data = {"product": product, "metadata": cleaned_data_packet['metadata']}
                json.dump(line_data, f)
                f.write('\n')

        # --- Stage 2: Update Database ---
        orchestrator = UpdateOrchestrator(self.mock_command, self.inbox_path)
        orchestrator.run()

        # --- Stage 3: Assert Database State ---
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Price.objects.count(), 1)

        product1 = Product.objects.get(name="Chocolate Chip Brioche Milk Rolls 8 Pack 280g")
        self.assertEqual(product1.brand, "BON APPETIT")
        self.assertEqual(sorted(product1.sizes), sorted(['280g', '8pk']))
        
        price1 = Price.objects.get(product=product1)
        self.assertEqual(price1.store, self.store)
        self.assertEqual(price1.price, Decimal('4.69'))
        self.assertFalse(price1.is_on_special)
        self.assertFalse(price1.is_available)
