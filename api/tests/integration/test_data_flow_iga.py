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
from api.utils.scraper_utils.DataCleanerIga import DataCleanerIga
from api.database_updating_classes.update_orchestrator import UpdateOrchestrator

RAW_IGA_PRODUCTS = [
  {
    "attributes": {},
    "available": True,
    "barcode": "9315090204483",
    "brand": "Australia's Own",
    "categories": [
      {
        "category": "Grocery",
        "categoryBreadcrumb": "Grocery",
        "categoryId": "df3c7713-38f0-40c3-84ad-757ff32c25d4",
        "retailerId": "Grocery"
      },
      {
        "category": "Drinks",
        "categoryBreadcrumb": "Grocery/Drinks",
        "categoryId": "79a1069b-5d11-4bcb-854f-b8dc8a98e1dd",
        "retailerId": "Drinks"
      },
      {
        "category": "Long Life Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk",
        "categoryId": "718c781b-ef40-46bf-ad12-8116b2f286c9",
        "retailerId": "Long_Life_Milk"
      },
      {
        "category": "Coconut Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk/Coconut Milk",
        "categoryId": "bebde1e3-167e-44cc-9879-bb2acb095a92",
        "retailerId": "Coconut_Milk"
      }
    ],
    "defaultCategory": [
      {
        "category": "Coconut Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk/Coconut Milk",
        "categoryId": "bebde1e3-167e-44cc-9879-bb2acb095a92",
        "retailerId": "Coconut_Milk"
      }
    ],
    "description": "Australian Natural Goodness<br /> <br />We believe Australia is packed full of nature's good stuff... from hiking in the bush, to strolling down a beach and wiggling your toes in the sand.<br /> <br />Australia's Own is all about the power of nature, nurturing us on the inside and feeling good on the outside. We only use pure and simple certified organic ingredients, 100% Australian made!<br /><br /> Our range of products is the way nature intended... simply good for you!<br /><br /><br />Organic farming, doing good for the planet.<br /> <br />- Chemical-free from synthetic herbicides and pesticides, growing cleaner food and saving our waterways. <br /><br />- Sustainable farming systems promoting greater biodiversity. <br /><br />- GMO's are prohibited on organic farms, ensuring methods of production are as close as nature intended.<br /><br />Allergen may be present: N/A <br /><br />Country of Origin: Made in Australia from at least 92% Australian ingredients",
    "image": {
      "cell": "https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/31218.jpg",
      "default": "https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/31218.jpg",
      "details": "https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/31218.jpg",
      "template": "https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/31218.jpg",
      "zoom": "https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/31218.jpg"
    },
    "isFavorite": False,
    "isPastPurchased": False,
    "name": "Australia's Own Organic Coconut Milk Unsweetened",
    "price": "$3.35",
    "priceLabel": "",
    "priceNumeric": 3.35,
    "pricePerUnit": "$3.35/l",
    "priceSource": "regular",
    "productId": "31218",
    "sellBy": "Each",
    "shoppingRuleMessages": None,
    "sku": "31218",
    "tprPrice": [],
    "unitOfMeasure": {
      "abbreviation": "l",
      "label": "Litre",
      "size": 1,
      "type": "litre"
    },
    "unitOfPrice": {
      "abbreviation": "",
      "label": "Each",
      "size": 1,
      "type": "each"
    },
    "unitOfSize": {
      "abbreviation": "l",
      "label": "Litre",
      "size": 1,
      "type": "litre"
    },
    "weightIncrement": None,
    "wholePrice": 3.35
  },
  {
    "attributes": {},
    "available": True,
    "barcode": "9556041641005",
    "brand": "Ayam",
    "categories": [
      {
        "category": "Grocery",
        "categoryBreadcrumb": "Grocery",
        "categoryId": "df3c7713-38f0-40c3-84ad-757ff32c25d4",
        "retailerId": "Grocery"
      },
      {
        "category": "Drinks",
        "categoryBreadcrumb": "Grocery/Drinks",
        "categoryId": "79a1069b-5d11-4bcb-854f-b8dc8a98e1dd",
        "retailerId": "Drinks"
      },
      {
        "category": "Long Life Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk",
        "categoryId": "718c781b-ef40-46bf-ad12-8116b2f286c9",
        "retailerId": "Long_Life_Milk"
      },
      {
        "category": "Coconut Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk/Coconut Milk",
        "categoryId": "bebde1e3-167e-44cc-9879-bb2acb095a92",
        "retailerId": "Coconut_Milk"
      }
    ],
    "defaultCategory": [
      {
        "category": "Coconut Milk",
        "categoryBreadcrumb": "Grocery/Drinks/Long Life Milk/Coconut Milk",
        "categoryId": "bebde1e3-167e-44cc-9879-bb2acb095a92",
        "retailerId": "Coconut_Milk"
      }
    ],
    "description": "",
    "image": {
      "cell": None,
      "default": None,
      "details": None,
      "template": None,
      "zoom": None
    },
    "isFavorite": False,
    "isPastPurchased": False,
    "name": "Ayam Coconut Cream Regular",
    "price": "$3.50",
    "priceLabel": "",
    "priceNumeric": 3.5,
    "pricePerUnit": "$1.75/100ml",
    "priceSource": "regular",
    "productId": "673701",
    "sellBy": "Each",
    "shoppingRuleMessages": None,
    "sku": "673701",
    "tprPrice": [],
    "unitOfMeasure": {
      "abbreviation": "ml",
      "label": "Millilitre",
      "size": 100,
      "type": "millilitre"
    },
    "unitOfPrice": {
      "abbreviation": "",
      "label": "Each",
      "size": 1,
      "type": "each"
    },
    "unitOfSize": {
      "abbreviation": "ml",
      "label": "Millilitre",
      "size": 200,
      "type": "millilitre"
    },
    "weightIncrement": None,
    "wholePrice": 3.5
  }
]

@override_settings(DEBUG=True)
class TestDataFlowIga(TestCase):

    def setUp(self):
        self.company = CompanyFactory(name="IGA")
        self.division = DivisionFactory(company=self.company)
        self.store = StoreFactory(company=self.company, division=self.division, store_name="IGA Test Store", store_id="5678")
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

    def test_iga_data_flow_from_inbox(self):
        # --- Stage 1: Create a realistic inbox file ---
        timestamp = datetime.now()
        cleaner = DataCleanerIga(
            raw_product_list=RAW_IGA_PRODUCTS,
            company=self.company.name,
            store_id=self.store.store_id,
            store_name=self.store.store_name,
            state=self.store.state,
            timestamp=timestamp
        )
        cleaned_data_packet = cleaner.clean_data()

        inbox_file_path = os.path.join(self.inbox_path, "iga_test.jsonl")
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

        # Product 1: Coconut Milk
        product1 = Product.objects.get(name="Australia's Own Organic Coconut Milk Unsweetened")
        self.assertEqual(product1.brand, "Australia's Own")
        self.assertEqual(sorted(product1.sizes), sorted(['1l', 'ea']))
        
        price1 = Price.objects.get(product=product1)
        self.assertEqual(price1.store, self.store)
        self.assertEqual(price1.price, Decimal('3.35'))
        self.assertFalse(price1.is_on_special)
        self.assertTrue(price1.is_available)

        # Product 2: Coconut Cream
        product2 = Product.objects.get(name="Ayam Coconut Cream Regular")
        self.assertEqual(product2.brand, "Ayam")
        self.assertEqual(sorted(product2.sizes), sorted(['200ml', 'ea']))

        price2 = Price.objects.get(product=product2)
        self.assertEqual(price2.store, self.store)
        self.assertEqual(price2.price, Decimal('3.50'))
        self.assertFalse(price2.is_on_special)
        self.assertTrue(price2.is_available)