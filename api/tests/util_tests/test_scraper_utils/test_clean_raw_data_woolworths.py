import json
from django.test import TestCase
from datetime import datetime
from api.utils.scraper_utils.clean_raw_data_woolworths import clean_raw_data_woolworths

class CleanRawDataWoolworthsTest(TestCase):
    def test_clean_raw_data_woolworths_full_data(self):
        raw_product_list = [
            {
                "Stockcode": "12345",
                "UrlFriendlyName": "test-product",
                "Barcode": "9300000000000",
                "Name": "Woolworths Test Product",
                "Brand": "Woolworths",
                "Description": "A short description.",
                "LargeImageFile": "image_large.jpg",
                "SmallImageFile": "image_small.jpg",
                "MediumImageFile": "image_medium.jpg",
                "Price": 5.50,
                "WasPrice": 6.00,
                "IsOnSpecial": True,
                "SavingsAmount": 0.50,
                "CentreTag": {"TagType": "Half Price"},
                "CupPrice": 1.10,
                "CupMeasure": "100g",
                "CupString": "$1.10 per 100g",
                "IsAvailable": True,
                "IsInStock": True,
                "SupplyLimit": 10,
                "PackageSize": "500g",
                "AdditionalAttributes": {
                    "description": "A long description.",
                    "countryoforigin": "Australia",
                    "healthstarrating": "4.5",
                    "ingredients": "Water, Sugar, Flour",
                    "allergenmaybepresent": "Gluten, Dairy",
                    "lifestyleanddietarystatement": "Vegan, Gluten Free",
                    "sapdepartmentname": "Fresh Food",
                    "sapcategoryname": "Fruit/Vegetables",
                    "sapsubcategoryname": "Apples",
                    "sapsegmentname": "Red Apples",
                    "piesdepartmentnamesjson": "[\"Pies Dept\"]",
                    "piescategorynamesjson": "[\"Pies Cat\"]",
                    "piessubcategorynamesjson": "[\"Pies SubCat\"]"
                },
                "Rating": {"Average": 4.2, "ReviewCount": 100},
                "IsNew": True,
                "ImageTag": {"FallbackText": "New Product"}
            }
        ]
        company = "Woolworths"
        store_id = "wool123"
        store_name = "Woolworths Metro"
        state = "NSW"
        category = "fruit"
        page_num = 1
        timestamp = datetime(2025, 8, 16, 12, 0, 0)

        cleaned_data = clean_raw_data_woolworths(raw_product_list, company, store_id, store_name, state, category, page_num, timestamp)

        self.assertIn('metadata', cleaned_data)
        self.assertIn('products', cleaned_data)
        self.assertEqual(len(cleaned_data['products']), 1)
        
        product = cleaned_data['products'][0]
        self.assertEqual(product['product_id_store'], "12345")
        self.assertEqual(product['barcode'], "9300000000000")
        self.assertEqual(product['name'], "Woolworths Test Product")
        self.assertEqual(product['brand'], "Woolworths")
        self.assertEqual(product['description_short'], "A short description.")
        self.assertEqual(product['description_long'], "A long description.")
        self.assertEqual(product['url'], "https://www.woolworths.com.au/shop/productdetails/12345/test-product")
        self.assertEqual(product['image_url_main'], "image_large.jpg")
        self.assertEqual(product['image_urls_all'], ["image_small.jpg", "image_medium.jpg", "image_large.jpg"])
        self.assertEqual(product['price_current'], 5.50)
        self.assertEqual(product['price_was'], 6.00)
        self.assertTrue(product['is_on_special'])
        self.assertEqual(product['price_save_amount'], 0.50)
        self.assertEqual(product['promotion_type'], "Half Price")
        self.assertEqual(product['price_unit'], 1.10)
        self.assertEqual(product['unit_of_measure'], "100g")
        self.assertEqual(product['unit_price_string'], "$1.10 per 100g")
        self.assertTrue(product['is_available'])
        self.assertEqual(product['stock_level'], "In Stock")
        self.assertEqual(product['purchase_limit'], 10)
        self.assertEqual(product['package_size'], "500g")
        self.assertEqual(product['country_of_origin'], "Australia")
        self.assertEqual(product['health_star_rating'], 4.5)
        self.assertEqual(product['ingredients'], "Water, Sugar, Flour")
        self.assertEqual(product['allergens_may_be_present'], ["Gluten", "Dairy"])
        self.assertEqual(product['category_path'], ["Fresh Food", "Fruit", "Vegetables", "Apples", "Red Apples"])
        self.assertIn("new", product['tags'])
        self.assertIn("Vegan", product['tags'])
        self.assertIn("Gluten Free", product['tags'])
        self.assertIn("New Product", product['tags'])
        self.assertEqual(product['rating_average'], 4.2)
        self.assertEqual(product['rating_count'], 100)

    def test_clean_raw_data_woolworths_minimal_data(self):
        raw_product_list = [
            {
                "Stockcode": "67890",
                "Name": "Minimal Product",
                "Price": 1.00,
                "IsAvailable": False,
                "IsInStock": False,
            }
        ]
        company = "Woolworths"
        store_id = "wool456"
        store_name = "Woolworths Express"
        state = "VIC"
        category = "dairy"
        page_num = 1
        timestamp = datetime(2025, 8, 16, 12, 0, 0)

        cleaned_data = clean_raw_data_woolworths(raw_product_list, company, store_id, store_name, state, category, page_num, timestamp)
        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]
        self.assertEqual(product['product_id_store'], "67890")
        self.assertEqual(product['name'], "Minimal Product")
        self.assertEqual(product['price_current'], 1.00)
        self.assertFalse(product['is_available'])
        self.assertEqual(product['stock_level'], "Out of Stock")
        self.assertEqual(product['category_path'], [])
        self.assertEqual(product['tags'], [])
        self.assertIsNone(product['url'])
        self.assertIsNone(product['image_url_main'])
        self.assertEqual(product['image_urls_all'], [])

    def test_clean_raw_data_woolworths_category_fallback(self):
        raw_product_list = [
            {
                "Stockcode": "111",
                "Name": "Fallback Category Product",
                "Price": 2.00,
                "AdditionalAttributes": {
                    "piesdepartmentnamesjson": "[\"Baked Goods\"]",
                    "piescategorynamesjson": "[\"Bread\"]",
                    "piessubcategorynamesjson": "[\"Loaves\"]"
                }
            }
        ]
        company = "Woolworths"
        store_id = "wool789"
        store_name = "Woolworths Local"
        state = "QLD"
        category = "bakery"
        page_num = 1
        timestamp = datetime(2025, 8, 16, 12, 0, 0)

        cleaned_data = clean_raw_data_woolworths(raw_product_list, company, store_id, store_name, state, category, page_num, timestamp)
        self.assertEqual(len(cleaned_data['products']), 1)
        product = cleaned_data['products'][0]
        self.assertEqual(product['category_path'], ["Baked Goods", "Bread", "Loaves"])

    def test_clean_raw_data_woolworths_empty_list(self):
        cleaned_data = clean_raw_data_woolworths([], "Woolworths", "id", "name", "state", "cat", 1, datetime.now())
        self.assertEqual(len(cleaned_data['products']), 0)
