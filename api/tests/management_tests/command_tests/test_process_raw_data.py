import os
import json
import tempfile
from datetime import datetime
from django.core.management import call_command
from django.test import TestCase, override_settings
from stores.models import Store, Category
from products.models import Product, Price

@override_settings(BASE_DIR=tempfile.gettempdir())
class TestProcessRawData(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_data_path = os.path.join(self.temp_dir.name, 'api', 'data', 'processed_data')
        self.archive_path = os.path.join(self.temp_dir.name, 'api', 'data', 'archive')
        os.makedirs(self.processed_data_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
        self.override = override_settings(BASE_DIR=self.temp_dir.name)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp_dir.cleanup()

    def test_handle_no_data(self):
        call_command('process_raw_data')
        self.assertEqual(Store.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Price.objects.count(), 0)

    def test_handle_with_data(self):
        store_name = "coles"
        store_dir = os.path.join(self.processed_data_path, store_name)
        os.makedirs(store_dir, exist_ok=True)
        file_name = "test_data.json"
        file_path = os.path.join(store_dir, file_name)

        scraped_at_time = datetime.now().isoformat()

        data = {
            "metadata": {
                "store": store_name,
                "scraped_at": scraped_at_time
            },
            "products": [
                {
                    "name": "Test Product 1",
                    "brand": "Test Brand",
                    "package_size": "1kg",
                    "price": 10.00,
                    "was_price": 12.00,
                    "is_on_special": True,
                    "barcode": "1234567890123",
                    "departments": [{"name": "Fruit & Veg", "id": "1"}],
                    "categories": [{"name": "Fruit", "id": "2"}],
                    "subcategories": [{"name": "Apples", "id": "3"}]
                },
                {
                    "name": "Test Product 2",
                    "brand": "Another Brand",
                    "package_size": "500g",
                    "price": 5.00,
                    "was_price": 5.00,
                    "is_on_special": False,
                    "barcode": "9876543210987",
                    "departments": [{"name": "Bakery"}],
                    "categories": [{"name": "Bread"}],
                    "subcategories": []
                }
            ]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        call_command('process_raw_data')

        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Store.objects.first().name, store_name.capitalize())

        self.assertEqual(Category.objects.count(), 5)
        self.assertTrue(Category.objects.filter(name="Fruit & Veg").exists())
        self.assertTrue(Category.objects.filter(name="Fruit").exists())
        self.assertTrue(Category.objects.filter(name="Apples").exists())
        self.assertTrue(Category.objects.filter(name="Bakery").exists())
        self.assertTrue(Category.objects.filter(name="Bread").exists())

        self.assertEqual(Product.objects.count(), 2)
        product1 = Product.objects.get(name="Test Product 1")
        self.assertEqual(product1.brand, "Test Brand")
        self.assertEqual(product1.category.name, "Apples")

        product2 = Product.objects.get(name="Test Product 2")
        self.assertEqual(product2.brand, "Another Brand")
        self.assertEqual(product2.category.name, "Bread")

        self.assertEqual(Price.objects.count(), 2)
        price1 = Price.objects.get(product=product1)
        self.assertEqual(price1.price, 10.00)
        self.assertEqual(price1.was_price, 12.00)
        self.assertTrue(price1.is_on_special)

        price2 = Price.objects.get(product=product2)
        self.assertEqual(price2.price, 5.00)
        self.assertFalse(price2.is_on_special)

        archive_file_path = os.path.join(self.archive_path, store_name, file_name)
        self.assertFalse(os.path.exists(file_path))
        self.assertTrue(os.path.exists(archive_file_path))

    def test_handle_empty_product_list(self):
        store_name = "woolworths"
        store_dir = os.path.join(self.processed_data_path, store_name)
        os.makedirs(store_dir, exist_ok=True)
        file_name = "empty.json"
        file_path = os.path.join(store_dir, file_name)

        data = {
            "metadata": {
                "store": store_name,
                "scraped_at": datetime.now().isoformat()
            },
            "products": []
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        call_command('process_raw_data')

        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Price.objects.count(), 0)
        self.assertFalse(os.path.exists(file_path))